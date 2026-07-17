import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

class SessionManager:
    """
    Tracks active sessions to allow global logout and concurrent session limits.
    """
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.max_concurrent_sessions = 3
        
    def create_session(self, user_id: str, device_info: str, ip_address: str) -> str:
        # Enforce max sessions
        user_sessions = self.get_user_sessions(user_id)
        if len(user_sessions) >= self.max_concurrent_sessions:
            # Revoke oldest
            oldest = min(user_sessions, key=lambda s: s["created_at"])
            self.revoke_session(oldest["session_id"])
            
        session_id = str(uuid.uuid4())
        self.active_sessions[session_id] = {
            "session_id": session_id,
            "user_id": user_id,
            "device_info": device_info,
            "ip_address": ip_address,
            "created_at": datetime.utcnow(),
            "last_active": datetime.utcnow()
        }
        return session_id
        
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        return [s for s in self.active_sessions.values() if s["user_id"] == user_id]
        
    def revoke_session(self, session_id: str) -> bool:
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return True
        return False
        
    def revoke_all_user_sessions(self, user_id: str):
        sessions = self.get_user_sessions(user_id)
        for s in sessions:
            self.revoke_session(s["session_id"])

session_manager = SessionManager()
