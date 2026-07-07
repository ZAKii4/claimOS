from typing import Callable, Any, Dict
from pydantic import Field
from app.workflows.nodes.base import BaseNode
from app.workflows.models import WorkflowContext


class ServiceTask(BaseNode):
    type: str = "ServiceTask"
    
    # We store the fully qualified name of the python function
    # e.g., "app.engines.ocr.run"
    action_name: str
    
    async def execute(self, context: WorkflowContext) -> Dict[str, Any]:
        # MVP: Simulation of service task execution
        # A real implementation would dynamically import and execute `self.action_name`
        return {f"{self.id}_completed": True}


class HumanTask(BaseNode):
    type: str = "HumanTask"
    assignee_role: str
    
    async def execute(self, context: WorkflowContext) -> Dict[str, Any]:
        # Human Tasks immediately suspend the workflow until resumed by an API call
        # A real implementation throws a SUSPEND signal or saves state and halts
        return {"assigned_to": self.assignee_role, f"{self.id}_pending": True}
