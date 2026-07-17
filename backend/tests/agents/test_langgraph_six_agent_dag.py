import asyncio

from app.agents.context import AgentContext
from app.agents.graph import GRAPH_EDGES, build_graph
from app.agents.registry import AgentRegistry
from app.agents.shared_memory import SharedMemory


def test_all_six_agents_are_discovered():
    registry = AgentRegistry()
    registry.discover()
    assert set(registry.get_all().keys()) == {
        "ocr_supervisor",
        "extraction_agent",
        "fraud_agent",
        "legal_agent",
        "decision_agent",
        "supervisor_agent",
    }


def test_graph_edges_match_the_documented_dag():
    deps_by_agent = dict(GRAPH_EDGES)

    assert deps_by_agent["ocr_supervisor"] == []
    assert deps_by_agent["extraction_agent"] == []
    assert deps_by_agent["fraud_agent"] == ["ocr_supervisor"]
    assert deps_by_agent["legal_agent"] == ["extraction_agent"]
    assert set(deps_by_agent["decision_agent"]) == {"fraud_agent", "legal_agent"}
    assert deps_by_agent["supervisor_agent"] == ["decision_agent"]


def test_graph_edges_only_reference_known_agents():
    known = {agent_id for agent_id, _ in GRAPH_EDGES}
    for agent_id, deps in GRAPH_EDGES:
        for dep in deps:
            assert dep in known, f"{agent_id} depends on unknown agent {dep}"


def test_build_graph_compiles_with_all_six_agents():
    registry = AgentRegistry()
    registry.discover()
    context = AgentContext(claim_id="C-1")
    memory = SharedMemory()

    graph = build_graph(registry.get_all(), context, memory)

    # Compiles without raising, and exposes the expected node ids (plus
    # LangGraph's implicit __start__/__end__ pseudo-nodes).
    node_ids = set(graph.get_graph().nodes.keys())
    assert {
        "ocr_supervisor",
        "extraction_agent",
        "fraud_agent",
        "legal_agent",
        "decision_agent",
        "supervisor_agent",
    } <= node_ids


def test_build_graph_degrades_gracefully_when_an_agent_is_missing():
    """
    Mirrors the old Planner's guard: a graph built from a partial agent set
    should compile and only include the nodes actually present, not error
    out because a dependency (e.g. decision_agent depending on legal_agent)
    is absent.
    """
    registry = AgentRegistry()
    registry.discover()
    agents = {
        agent_id: agent
        for agent_id, agent in registry.get_all().items()
        if agent_id != "legal_agent"
    }
    context = AgentContext(claim_id="C-1")
    memory = SharedMemory()

    graph = build_graph(agents, context, memory)
    node_ids = set(graph.get_graph().nodes.keys())

    assert "legal_agent" not in node_ids
    assert "decision_agent" in node_ids  # still compiles, just loses that one dependency


def test_full_graph_runs_end_to_end_without_a_document():
    """
    Same scenario as the old scheduler-based test: no image_path in raw
    data, so ocr_supervisor must fail explicitly and fraud_agent must skip
    — and the graph must still complete rather than deadlock, now that
    LangGraph (not a hand-rolled asyncio loop) drives execution.
    """
    registry = AgentRegistry()
    registry.discover()
    context = AgentContext(claim_id="C-1", metadata={"raw": {"doc": "invoice"}})
    memory = SharedMemory()

    graph = build_graph(registry.get_all(), context, memory)
    final_state = asyncio.run(graph.ainvoke({"results": {}}))
    results = final_state["results"]

    assert results["ocr_supervisor"].status == "FAILED"
    assert results["fraud_agent"] is None  # skipped: no OCR text to analyze
    assert "fraud_score" not in context.metadata
