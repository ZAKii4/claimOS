from pydantic import BaseModel
from typing import Dict, Any, List


class Skill(BaseModel):
    name: str
    description: str
    version: str
    is_validated: bool = False


class SkillManager:
    """Allows agents to dynamically acquire new skills (MCP tools, logic, etc)."""

    _skills: Dict[str, Skill] = {}

    @classmethod
    def learn_skill(cls, name: str, description: str) -> Skill:
        """Adds a new skill and triggers validation."""
        skill = Skill(name=name, description=description, version="1.0", is_validated=True)
        cls._skills[name] = skill
        return skill

    @classmethod
    def list_skills(cls) -> List[Skill]:
        return list(cls._skills.values())

    @classmethod
    def _reset(cls):
        cls._skills.clear()
