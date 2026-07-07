import asyncio
from typing import Dict, Any
from app.agents.manager import AgentManager


class AgentOrchestrationStep:
    """
    Integrates the new Multi-Agent platform into the existing pipeline (if needed),
    or acts as the main entrypoint.
    """
    def __init__(self):
        self.manager = AgentManager()
        
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the agent manager synchronously for pipeline compatibility,
        or handles it async if the pipeline allows.
        """
        claim_id = context.get("claim_id", "unknown_claim")
        raw_data = context.get("raw_data", {})
        
        # We run the async process in a synchronous context if called by the legacy pipeline
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
            
        if loop and loop.is_running():
            # Already in an event loop, create task
            # Note: in a true async pipeline, this step would be async def execute()
            task = loop.create_task(self.manager.process_claim(claim_id, raw_data))
            context["agent_orchestration_task"] = task
        else:
            result = asyncio.run(self.manager.process_claim(claim_id, raw_data))
            context["agent_orchestration_result"] = result
            
        return context
