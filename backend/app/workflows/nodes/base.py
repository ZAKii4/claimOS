from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from app.workflows.models import WorkflowContext


class BaseNode(BaseModel):
    id: str
    name: str
    type: str

    async def execute(self, context: WorkflowContext) -> Dict[str, Any]:
        """Execute node logic. Returns updates for the context."""
        return {}
        
    async def compensate(self, context: WorkflowContext) -> None:
        """Undo logic if the workflow fails downstream."""
        pass
