from enum import Enum
from typing import Dict, Any, List
from pydantic import BaseModel, Field
import uuid


class MemoryType(str, Enum):
    WORKING = "WORKING"      # Context of current task
    EPISODIC = "EPISODIC"    # Past events, executed plans
    SEMANTIC = "SEMANTIC"    # Extracted knowledge (facts, rules)


class MemoryRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    agent_id: str
    m_type: MemoryType
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemoryManager:
    """Manages the agent's persistent and temporary memory."""

    _memories: List[MemoryRecord] = []

    @classmethod
    def store(cls, tenant_id: str, agent_id: str, m_type: MemoryType, content: str, metadata: Dict[str, Any] = None) -> MemoryRecord:
        record = MemoryRecord(
            tenant_id=tenant_id,
            agent_id=agent_id,
            m_type=m_type,
            content=content,
            metadata=metadata or {}
        )
        cls._memories.append(record)
        return record

    @classmethod
    def retrieve(cls, tenant_id: str, agent_id: str, m_type: MemoryType) -> List[MemoryRecord]:
        return [m for m in cls._memories if m.tenant_id == tenant_id and m.agent_id == agent_id and m.m_type == m_type]

    @classmethod
    def consolidate_working_to_episodic(cls, tenant_id: str, agent_id: str, context_id: str):
        """Moves working memory regarding a context to episodic memory."""
        working = [m for m in cls._memories if m.tenant_id == tenant_id and m.agent_id == agent_id and m.m_type == MemoryType.WORKING and m.metadata.get("context_id") == context_id]
        
        if not working:
            return

        combined_content = " | ".join(m.content for m in working)
        cls.store(tenant_id, agent_id, MemoryType.EPISODIC, combined_content, {"context_id": context_id})

        # Clear working memory for this context
        cls._memories = [m for m in cls._memories if not (m in working)]

    @classmethod
    def _clear_all(cls):
        cls._memories.clear()
