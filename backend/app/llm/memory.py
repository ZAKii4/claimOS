from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from app.llm.models import Message


class ConversationHistory(BaseModel):
    session_id: str
    messages: List[Message] = Field(default_factory=list)
    summary: Optional[str] = None
    
    def add_message(self, message: Message):
        self.messages.append(message)


class ConversationMemory:
    """MVP Memory Manager mapping sessions to histories."""
    
    def __init__(self):
        self._sessions: Dict[str, ConversationHistory] = {}
        
    def get_session(self, session_id: str) -> ConversationHistory:
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationHistory(session_id=session_id)
        return self._sessions[session_id]
        
    def save_message(self, session_id: str, message: Message):
        session = self.get_session(session_id)
        session.add_message(message)
