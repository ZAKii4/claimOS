import uuid
from typing import List, Dict, Any

class ConversationMemory:
    """
    Handles Conversation Store and Semantic Cache for agents.
    """
    def __init__(self):
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
        self.semantic_cache = {} # Mocks pgvector cache
        
    def add_message(self, session_id: str, role: str, content: str):
        if session_id not in self.sessions:
            self.sessions[session_id] = []
            
        self.sessions[session_id].append({"role": role, "content": content})
        
    def get_history(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        if session_id not in self.sessions:
            return []
        return self.sessions[session_id][-limit:]
        
    def check_semantic_cache(self, query: str) -> str:
        # Mock semantic cache hit
        if "franchise" in query.lower() and "dupont" in query.lower():
            return "La franchise de M. Dupont est de 150€."
        return None

conversation_memory = ConversationMemory()
