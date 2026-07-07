from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.agents.context import AgentContext
from app.agents.memory import SharedMemory

class AgentResult(BaseModel):
    status: str  # SUCCESS, FAILED, SKIPPED
    confidence: float
    execution_time_ms: int
    artifacts: Dict[str, Any]
    messages: List[str]


class BaseAgent(ABC):
    id: str
    name: str
    version: str
    capabilities: List[str]
    
    def health_check(self) -> bool:
        return True
        
    @abstractmethod
    async def plan(self, context: AgentContext, memory: SharedMemory) -> bool:
        """Determines if the agent should execute based on current context."""
        pass
        
    @abstractmethod
    async def execute(self, context: AgentContext, memory: SharedMemory) -> AgentResult:
        """The main execution logic of the agent."""
        pass
        
    @abstractmethod
    async def validate(self, result: AgentResult) -> bool:
        """Validates its own result."""
        pass
        
    async def rollback(self, context: AgentContext, memory: SharedMemory) -> None:
        """Reverts any changes if necessary."""
        pass
