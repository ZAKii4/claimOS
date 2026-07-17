from pydantic import BaseModel
from typing import List


class ExecutionPlan(BaseModel):
    name: str
    estimated_cost: float
    estimated_time_sec: int
    quality_score: float
    risk_level: str


class DynamicPlanningEngine:
    """Generates and evaluates multiple execution plans dynamically."""

    @classmethod
    def generate_plans(cls, objective: str) -> List[ExecutionPlan]:
        """Mocks generating multiple execution strategies."""
        return [
            ExecutionPlan(name="Fast Path", estimated_cost=0.01, estimated_time_sec=2, quality_score=0.75, risk_level="HIGH"),
            ExecutionPlan(name="Balanced Path", estimated_cost=0.05, estimated_time_sec=10, quality_score=0.90, risk_level="MEDIUM"),
            ExecutionPlan(name="Deep Reasoning Path", estimated_cost=0.15, estimated_time_sec=45, quality_score=0.99, risk_level="LOW")
        ]

    @classmethod
    def select_best_plan(cls, plans: List[ExecutionPlan], strategy: str = "BALANCED") -> ExecutionPlan:
        """Selects the best plan based on the strategy."""
        if not plans:
            raise ValueError("No plans generated")
            
        if strategy == "SPEED":
            return min(plans, key=lambda p: p.estimated_time_sec)
        elif strategy == "QUALITY":
            return max(plans, key=lambda p: p.quality_score)
        else:
            # BALANCED: maximize quality while minimizing cost
            return max(plans, key=lambda p: p.quality_score - p.estimated_cost)
