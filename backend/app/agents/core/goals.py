from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import uuid


class GoalStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"


class Goal(BaseModel):
    """Represents an autonomous agent's objective."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    description: str
    status: GoalStatus = GoalStatus.PENDING
    priority: int = 1
    dependencies: List[str] = Field(default_factory=list)  # list of goal IDs
    constraints: Dict[str, Any] = Field(default_factory=dict)
    deadline: Optional[datetime] = None
    cost_estimate: float = 0.0
    confidence: float = 1.0
    sub_goals: List["Goal"] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    def add_subgoal(self, goal: "Goal"):
        self.sub_goals.append(goal)

    def is_blocked(self) -> bool:
        # Simplification: blocked if it has dependencies that are not completed (not checked here directly, left to engine)
        return False
