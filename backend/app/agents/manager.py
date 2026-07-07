from typing import Dict, Any
from app.agents.registry import AgentRegistry
from app.agents.planner import Planner
from app.agents.scheduler import Scheduler
from app.agents.communication import EventBus
from app.agents.context import AgentContext
from app.agents.memory import SharedMemory
from app.agents.monitor import AgentMonitor
from app.agents.history import AgentHistory


class AgentManager:
    """
    The orchestrator that ties the multi-agent system together.
    """
    def __init__(self):
        self.registry = AgentRegistry()
        self.registry.discover()
        
        self.planner = Planner(self.registry)
        self.scheduler = Scheduler(self.registry)
        self.event_bus = EventBus()
        self.monitor = AgentMonitor()
        
    async def process_claim(self, claim_id: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entrypoint replacing the traditional sequential pipeline.
        """
        # 1. Initialize State
        context = AgentContext(claim_id=claim_id, metadata={"raw": raw_data})
        memory = SharedMemory()
        history = AgentHistory(claim_id=claim_id)
        
        # 2. Planning Phase
        graph = await self.planner.create_plan(context)
        
        # 3. Execution Phase
        # The scheduler handles async execution and dependencies
        results = await self.scheduler.execute_graph(graph, context, memory)
        
        # 4. Aggregation & Metrics
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
