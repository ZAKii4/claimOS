from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime

class Observation(BaseModel):
    agent_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any]
    confidence: float

class SharedMemory(BaseModel):
    """
    Common memory bank for agents to read and write observations, 
    hypotheses, and intermediate results.
    """
    observations: List[Observation] = Field(default_factory=list)
    hypotheses: List[Dict[str, Any]] = Field(default_factory=list)
    
    def add_observation(self, agent_id: str, data: Dict[str, Any], confidence: float = 1.0):
        self.observations.append(Observation(agent_id=agent_id, data=data, confidence=confidence))
        
    def get_observations_by_agent(self, agent_id: str) -> List[Observation]:
        return [o for o in self.observations if o.agent_id == agent_id]
