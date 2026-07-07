from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class WorkflowState(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"


class TaskState(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    COMPENSATED = "COMPENSATED"


class WorkflowContext(BaseModel):
    variables: Dict[str, Any] = Field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.variables.get(key, default)
        
    def set(self, key: str, value: Any):
        self.variables[key] = value


class WorkflowEdge(BaseModel):
    source_id: str
    target_id: str
    condition_expression: Optional[str] = None # e.g. "claim.amount > 50"


class WorkflowDefinition(BaseModel):
    id: str
    name: str
    version: int = 1
    nodes: List[Any] = Field(default_factory=list) # List of WorkflowNode
    edges: List[WorkflowEdge] = Field(default_factory=list)
    start_node_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WorkflowTaskExecution(BaseModel):
    task_id: str
    node_id: str
    state: TaskState = TaskState.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error: Optional[str] = None


class WorkflowInstance(BaseModel):
    id: str
    definition_id: str
    state: WorkflowState = WorkflowState.PENDING
    context: WorkflowContext = Field(default_factory=WorkflowContext)
    task_executions: Dict[str, WorkflowTaskExecution] = Field(default_factory=dict)
    current_node_ids: List[str] = Field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error: Optional[str] = None
