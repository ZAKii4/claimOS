from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List

from app.optimization.core.recommendation import RecommendationEngine
from app.optimization.ai.selection import ModelSelectionEngine
from app.optimization.ai.prompts import PromptOptimizer
from app.optimization.ai.benchmark import BenchmarkEngine
from app.optimization.ai.experiments import ExperimentManager
from app.optimization.financial.capacity import CapacityPlanningEngine
from app.optimization.financial.cost import CostOptimizationEngine

router = APIRouter(prefix="/optimization", tags=["Enterprise AI Operations & Optimization"])


class ExperimentRequest(BaseModel):
    tenant_id: str
    name: str
    parameters: Dict[str, Any]


class PromptEvalRequest(BaseModel):
    tenant_id: str
    task_name: str
    test_data: Dict[str, Any]


@router.get("/recommendations")
def get_recommendations(tenant_id: str):
    """Produces automatic recommendations for cost and performance."""
    return RecommendationEngine.generate_recommendations(tenant_id)


@router.get("/benchmarks")
def get_benchmarks(component: str):
    """Gets the benchmark leaderboard for a specific component (e.g., LLM, OCR)."""
    return BenchmarkEngine.run_benchmark(component)


@router.post("/experiments")
def log_experiment(req: ExperimentRequest):
    """Logs a new AI experiment or hyperparameter tuning run."""
    exp = ExperimentManager.log_experiment(req.tenant_id, req.name, req.parameters)
    return {"id": exp.id, "status": "Logged"}


@router.get("/capacity")
def get_capacity_forecast(tenant_id: str):
    """Forecasts resource saturation (CPU, LLM quota, etc)."""
    return CapacityPlanningEngine.forecast_capacity(tenant_id)


@router.get("/costs/optimization")
def get_cost_optimizations(tenant_id: str):
    """Suggests ways to reduce operational costs."""
    return CostOptimizationEngine.analyze_costs(tenant_id)


@router.post("/prompts/evaluate")
def evaluate_prompts(req: PromptEvalRequest):
    """Runs A/B testing on prompt variants and returns the winner."""
    return PromptOptimizer.evaluate_multiple(req.tenant_id, req.task_name, req.test_data)


@router.get("/models/select")
def select_model(component: str, priority: str = "BALANCED"):
    """Dynamically selects the best AI model based on context constraints."""
    context = {"priority": priority.upper()}
    model = ModelSelectionEngine.select_model(component, context)
    return {"selected_model": model.name, "latency": model.avg_latency_ms, "cost": model.cost_per_unit}
