from pydantic import BaseModel, Field
from typing import List, Dict, Any
import uuid


class AITeam(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    manager: str
    agents: List[str]
    reviewer: str
    quality_supervisor: str
    status: str = "ACTIVE"


class AIOrganizationEngine:
    """Manages the hierarchy and structure of AI teams."""

    _teams: Dict[str, AITeam] = {}

    @classmethod
    def get_organization_structure(cls) -> Dict[str, Any]:
        """Returns the full AI organization structure."""
        return {
            "total_teams": len(cls._teams),
            "teams": [t.model_dump() for t in cls._teams.values()]
        }

    @classmethod
    def create_team(cls, name: str, manager: str, agents: List[str]) -> AITeam:
        """Dynamically creates a new specialized team."""
        team = AITeam(
            name=name,
            manager=manager,
            agents=agents,
            reviewer=f"Reviewer_{name}",
            quality_supervisor=f"Quality_{name}"
        )
        cls._teams[team.id] = team
        return team

    @classmethod
    def dissolve_team(cls, team_id: str) -> bool:
        """Dissolves an existing team."""
        if team_id in cls._teams:
            cls._teams[team_id].status = "DISSOLVED"
            return True
        return False

    @classmethod
    def _reset(cls):
        cls._teams.clear()
