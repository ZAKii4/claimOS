from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import uuid
from datetime import datetime, timezone


class PromptVersion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    version_tag: str
    is_active: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PromptRepository:
    """Stores and versions system prompts for agents."""

    _prompts: Dict[str, List[PromptVersion]] = {}

    @classmethod
    def add_prompt(cls, agent_name: str, content: str, version_tag: str) -> PromptVersion:
        if agent_name not in cls._prompts:
            cls._prompts[agent_name] = []
            
        # Deactivate all others
        for p in cls._prompts[agent_name]:
            p.is_active = False
            
        new_p = PromptVersion(content=content, version_tag=version_tag, is_active=True)
        cls._prompts[agent_name].append(new_p)
        return new_p

    @classmethod
    def get_active_prompt(cls, agent_name: str) -> Optional[PromptVersion]:
        prompts = cls._prompts.get(agent_name, [])
        for p in prompts:
            if p.is_active:
                return p
        return None

    @classmethod
    def rollback_prompt(cls, agent_name: str, version_tag: str) -> bool:
        prompts = cls._prompts.get(agent_name, [])
        found = False
        for p in prompts:
            if p.version_tag == version_tag:
                found = True
                p.is_active = True
            else:
                p.is_active = False
        return found

    @classmethod
    def _reset(cls):
        cls._prompts.clear()
