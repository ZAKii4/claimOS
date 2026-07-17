from typing import Any

from app.agents.communication import EventBus
from app.agents.context import AgentContext
from app.agents.graph import build_graph
from app.agents.history import AgentHistory
from app.agents.monitor import AgentMonitor
from app.agents.registry import AgentRegistry
from app.agents.shared_memory import SharedMemory


class AgentManager:
    """
    The orchestrator that ties the multi-agent system together.

    Execution is delegated to LangGraph (app/agents/graph.py) — see
    docs/COURS_08_LANGGRAPH_ET_MODELES.md for why the previous hand-rolled
    Planner/Scheduler was replaced rather than kept alongside it.
    """
    def __init__(self):
        self.registry = AgentRegistry()
        self.registry.discover()

        self.event_bus = EventBus()
        self.monitor = AgentMonitor()

    async def process_claim(self, claim_id: str, raw_data: dict[str, Any]) -> dict[str, Any]:
        """
        Main entrypoint replacing the traditional sequential pipeline.
        """
        # 1. Initialize State
        context = AgentContext(claim_id=claim_id, metadata={"raw": raw_data})
        memory = SharedMemory()
        history = AgentHistory(claim_id=claim_id)

        # 2. Compile and run the LangGraph DAG for whichever agents are
        # registered — same dependency shape the old Planner encoded.
        graph = build_graph(self.registry.get_all(), context, memory)
        final_state = await graph.ainvoke({"results": {}})
        results = final_state["results"]

        # 3. Aggregation & Metrics
        for agent_id, result in results.items():
            success = result.status == "SUCCESS" if result else False
            duration = result.execution_time_ms if result else 0

            self.monitor.record_execution(agent_id, success, duration)
            history.log_action(agent_id, "EXECUTE", "SUCCESS" if success else "FAILED", duration)

        return {
            "status": "COMPLETED",
            "context": context.model_dump(),
            "history": history.model_dump(),
            "agent_results": {k: v.model_dump() if v else None for k, v in results.items()}
        }
