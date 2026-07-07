from pydantic import BaseModel, Field
from typing import Dict, Any, List
from datetime import datetime

class ActionLog(BaseModel):
    agent_id: str
    action_type: str  # PLAN, EXECUTE, VALIDATE, ROLLBACK
    status: str
    duration_ms: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = Field(default_factory=dict)
    
class AgentHistory(BaseModel):
    """
    Tracks the full lifecycle of agent execution for a specific claim.
    """
    claim_id: str
    logs: List[ActionLog] = Field(default_factory=list)
    
    def log_action(self, agent_id: str, action: str, status: str, duration_ms: int, details: dict = None):
        self.logs.append(
            ActionLog(
                agent_id=agent_id,
                action_type=action,
                status=status,
                duration_ms=duration_ms,
                details=details or {}
            )
        )
