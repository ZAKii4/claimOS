from fastapi import APIRouter
from typing import List, Dict, Any
from pydantic import BaseModel

from app.autonomous.organization.teams import AIOrganizationEngine, AITeam
from app.autonomous.organization.workforce import WorkforceManager
from app.autonomous.memory.enterprise import EnterpriseMemoryEngine
from app.autonomous.memory.evolution import KnowledgeEvolutionEngine
from app.autonomous.skills.manager import SkillManager, Skill
from app.autonomous.reasoning.meta import MetaReasoningEngine
from app.autonomous.governance.autonomous import AutonomousGovernanceEngine
from app.autonomous.laboratory.lab import AILabEngine

router = APIRouter(prefix="/autonomous", tags=["Enterprise Autonomous AI"])


class TeamCreateRequest(BaseModel):
    name: str
    manager: str
    agents: List[str]


class SkillRequest(BaseModel):
    name: str
    description: str


class MetaReasoningRequest(BaseModel):
    trace: dict


class GovernanceRequest(BaseModel):
    agent_id: str
    action_details: dict


class BenchmarkRequest(BaseModel):
    candidates: List[str]
    metric: str


@router.get("/organization")
def get_organization():
    """Returns the full AI organization structure."""
    return AIOrganizationEngine.get_organization_structure()


@router.get("/teams")
def list_teams():
    """Returns list of active AI teams."""
    return AIOrganizationEngine.get_organization_structure()["teams"]


@router.post("/teams/create", response_model=AITeam)
def create_team(req: TeamCreateRequest):
    """Dynamically creates a new AI team."""
    return AIOrganizationEngine.create_team(req.name, req.manager, req.agents)


@router.post("/skills", response_model=Skill)
def add_skill(req: SkillRequest):
    """Adds a new skill to the AI organization."""
    return SkillManager.learn_skill(req.name, req.description)


@router.get("/memory/global")
def get_global_memory():
    """Returns the consolidated enterprise memory."""
    return EnterpriseMemoryEngine.get_memory()


@router.post("/meta-reasoning")
def analyze_reasoning(req: MetaReasoningRequest):
    """Analyzes past reasoning to improve future strategies."""
    return MetaReasoningEngine.analyze_reasoning_trace(req.trace)


@router.post("/governance")
def enforce_governance(req: GovernanceRequest):
    """Evaluates an action autonomously for compliance and safety."""
    return AutonomousGovernanceEngine.evaluate_action(req.agent_id, req.action_details)


@router.post("/laboratory")
def run_benchmark(req: BenchmarkRequest):
    """Runs a benchmark comparing models or prompts."""
    return AILabEngine.run_benchmark(req.candidates, req.metric)


@router.get("/command-center")
def get_command_center():
    """Global dashboard showing the status of the autonomous organization."""
    return {
        "status": "AUTONOMOUS_MODE_ACTIVE",
        "workforce": AIOrganizationEngine.get_organization_structure(),
        "skills_count": len(SkillManager.list_skills()),
        "memory_size": len(EnterpriseMemoryEngine.get_memory()),
        "laboratory": "IDLE",
        "governance_status": "SECURE"
    }
