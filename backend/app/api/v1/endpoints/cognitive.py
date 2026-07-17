from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel

from app.acos.orchestrator.orchestrator import CognitiveOrchestrator, CognitiveObjective
from app.acos.orchestrator.planner import DynamicPlanningEngine, ExecutionPlan
from app.acos.orchestrator.tools import ToolSelectionEngine
from app.acos.reasoning.engine import MultiStepReasoningEngine
from app.acos.memory.consolidation import MemoryConsolidationEngine
from app.acos.healing.engine import SelfHealingEngine
from app.acos.quality.scorecard import EnterpriseScorecard

router = APIRouter(prefix="/cognitive", tags=["Enterprise ACOS"])


class ObjectiveRequest(BaseModel):
    id: str
    description: str
    priority: str


class PlanRequest(BaseModel):
    objective: str


class ReasonRequest(BaseModel):
    problem: str
    strategy: str = "CoT"


class ToolSelectRequest(BaseModel):
    task: str


class MemoryRequest(BaseModel):
    short_term: List[Dict[str, Any]]
    episodic: List[Dict[str, Any]]


class HealRequest(BaseModel):
    error_type: str
    context: dict


class ScorecardRequest(BaseModel):
    task_id: str
    metrics: dict


@router.post("/objectives")
def create_objective(req: ObjectiveRequest):
    obj = CognitiveObjective(id=req.id, description=req.description, priority=req.priority)
    res = CognitiveOrchestrator.execute_objective(obj)
    return res


@router.post("/plan", response_model=List[ExecutionPlan])
def generate_plan(req: PlanRequest):
    return DynamicPlanningEngine.generate_plans(req.objective)


@router.post("/reason")
def trigger_reasoning(req: ReasonRequest):
    try:
        return MultiStepReasoningEngine.execute_reasoning(req.problem, req.strategy)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tools/select")
def select_tools(req: ToolSelectRequest):
    tools = ToolSelectionEngine.select_tools(req.task)
    return {"task": req.task, "selected_tools": tools}


@router.post("/memory")
def consolidate_memory(req: MemoryRequest):
    return MemoryConsolidationEngine.consolidate(req.short_term, req.episodic)


@router.post("/reflection")
def run_reflection(req: ReasonRequest):
    return MultiStepReasoningEngine.execute_reasoning(req.problem, "Reflection")


@router.post("/heal")
def self_heal(req: HealRequest):
    return SelfHealingEngine.analyze_and_heal(req.error_type, req.context)


@router.post("/scorecard")
def generate_scorecard(req: ScorecardRequest):
    return EnterpriseScorecard.generate_scorecard(req.task_id, req.metrics)


@router.get("/dashboard")
def get_dashboard():
    return {
        "status": "ONLINE",
        "active_agents": 12,
        "active_objectives": 3,
        "mcp_servers": 4,
        "overall_health": "OPTIMAL"
    }
