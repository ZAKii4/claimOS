from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


class Observation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    agent_id: str
    context_id: str  # e.g., claim_id
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1


class CollaborationManager:
    """Provides a shared workspace for agents to share observations and collaborate."""

    _observations: List[Observation] = []

    @classmethod
    def share_observation(cls, tenant_id: str, agent_id: str, context_id: str, content: str) -> Observation:
        obs = Observation(
            tenant_id=tenant_id,
            agent_id=agent_id,
            context_id=context_id,
            content=content
        )
        cls._observations.append(obs)
        return obs

    @classmethod
    def get_context_observations(cls, tenant_id: str, context_id: str) -> List[Observation]:
        return [o for o in cls._observations if o.tenant_id == tenant_id and o.context_id == context_id]

    @classmethod
    def _clear_all(cls):
        cls._observations.clear()
