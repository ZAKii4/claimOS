"""
LangGraph-based orchestration for the 6-agent claim collaboration pipeline.

Replaces the hand-rolled ``Planner``/``Scheduler`` pair (deleted — see
docs/COURS_08_LANGGRAPH_ET_MODELES.md) with LangGraph's ``StateGraph``,
which already provides exactly what the hand-rolled scheduler was
reimplementing: fan-out/fan-in DAG execution, waiting for all of a node's
predecessors before running it, and async node support.

Graph shape (identical DAG documented in docs/COURS_04_AGENTS.md — only the
execution engine changed, not the dependency structure):

            ocr_supervisor        extraction_agent
                  |                       |
                  v                       v
             fraud_agent            legal_agent
                  \\                     /
                   v                   v
                    decision_agent
                          |
                          v
                   supervisor_agent

Design note — why ``context``/``memory`` are NOT part of the LangGraph state:
``AgentContext`` and ``SharedMemory`` are mutable objects every ``BaseAgent``
already mutates in place (``context.ocr_results = ...``,
``memory.add_observation(...)``) — exactly how the old Scheduler shared them.
Threading them through LangGraph's state (which merges per-key updates
across parallel branches) would need a reducer for every field two
concurrent nodes might touch, for no benefit: they're the same Python object
throughout the whole run regardless. They're captured once via closure
(``_make_node``) instead. Only ``results`` — one ``AgentResult`` per agent —
needs LangGraph-managed state, since ``ocr_supervisor`` and
``extraction_agent`` both write to it in the same superstep (they have no
dependency on each other) and therefore need a merge reducer rather than
last-write-wins.
"""

from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.base import AgentResult, BaseAgent
from app.agents.context import AgentContext
from app.agents.shared_memory import SharedMemory

# (agent_id, [dependency_agent_ids]) — the graph's source of truth. Kept as
# a plain module-level constant (rather than buried in build_graph) so tests
# can assert the dependency structure without introspecting a compiled
# LangGraph object.
GRAPH_EDGES: list[tuple[str, list[str]]] = [
    ("ocr_supervisor", []),
    ("extraction_agent", []),
    ("fraud_agent", ["ocr_supervisor"]),
    ("legal_agent", ["extraction_agent"]),
    ("decision_agent", ["fraud_agent", "legal_agent"]),
    ("supervisor_agent", ["decision_agent"]),
]


def _merge_results(
    left: dict[str, AgentResult | None], right: dict[str, AgentResult | None]
) -> dict[str, AgentResult | None]:
    merged = dict(left)
    merged.update(right)
    return merged


class GraphState(TypedDict):
    results: Annotated[dict[str, AgentResult | None], _merge_results]


def _make_node(agent: BaseAgent, context: AgentContext, memory: SharedMemory):
    """
    Wraps one BaseAgent's plan/execute/validate/rollback cycle as a
    LangGraph node function — identical semantics to the old
    Scheduler._run_agent(), just invoked by LangGraph instead of a hand
    -rolled asyncio.wait loop.
    """

    async def node(state: GraphState) -> dict:
        if not agent.health_check():
            return {"results": {agent.id: None}}

        should_run = await agent.plan(context, memory)
        if not should_run:
            return {"results": {agent.id: None}}

        result = await agent.execute(context, memory)
        is_valid = await agent.validate(result)
        if not is_valid:
            await agent.rollback(context, memory)

        return {"results": {agent.id: result}}

    return node


def build_graph(
    agents: dict[str, BaseAgent], context: AgentContext, memory: SharedMemory
) -> CompiledStateGraph:
    """
    Compiles a LangGraph StateGraph for whichever of the 6 agents are
    actually registered. Mirrors the old Planner's degrade-gracefully
    behavior: an agent that isn't registered has its node — and every edge
    naming it — silently skipped rather than failing to compile.
    """
    builder = StateGraph(GraphState)
    present = {agent_id for agent_id, _ in GRAPH_EDGES if agent_id in agents}

    for agent_id in present:
        builder.add_node(agent_id, _make_node(agents[agent_id], context, memory))

    nodes_with_outgoing: set[str] = set()
    for agent_id, deps in GRAPH_EDGES:
        if agent_id not in present:
            continue
        deps_present = [d for d in deps if d in present]
        if not deps_present:
            builder.add_edge(START, agent_id)
        else:
            for dep in deps_present:
                builder.add_edge(dep, agent_id)
                nodes_with_outgoing.add(dep)

    # Every node needs a path to END or LangGraph refuses to compile the
    # graph — only nodes nothing else depends on (leaves) need it added
    # explicitly; the rest already have an outgoing edge to their dependent.
    for agent_id in present:
        if agent_id not in nodes_with_outgoing:
            builder.add_edge(agent_id, END)

    return builder.compile()
