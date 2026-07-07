from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

class AgentEvent(BaseModel):
    event_type: str
    source_agent_id: str
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AgentMessage(BaseModel):
    id: str
    sender_id: str
    target_id: Optional[str]
    content: Dict[str, Any]
    reply_to: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
