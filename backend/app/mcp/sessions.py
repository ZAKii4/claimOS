from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import uuid


class MCPSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    server_id: str
    status: str = "ACTIVE"
    history: List[Dict[str, Any]] = Field(default_factory=list)


class MCPSessionManager:
    """Manages MCP sessions and contexts."""

    _sessions: Dict[str, MCPSession] = {}

    @classmethod
    def create_session(cls, server_id: str) -> MCPSession:
        session = MCPSession(server_id=server_id)
        cls._sessions[session.id] = session
        return session

    @classmethod
    def get_session(cls, session_id: str) -> Optional[MCPSession]:
        return cls._sessions.get(session_id)

    @classmethod
    def append_to_history(cls, session_id: str, entry: Dict[str, Any]) -> bool:
        session = cls.get_session(session_id)
        if session:
            session.history.append(entry)
            return True
        return False

    @classmethod
    def resume_session(cls, session_id: str) -> Dict[str, Any]:
        session = cls.get_session(session_id)
        if not session:
            return {"status": "ERROR", "message": "Session not found"}
        session.status = "ACTIVE"
        return {"status": "RESUMED", "session_id": session_id}
