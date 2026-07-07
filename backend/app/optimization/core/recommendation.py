from typing import List, Dict, Any
from pydantic import BaseModel, Field
import uuid
from app.optimization.core.manager import OptimizationManager


class Recommendation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    category: str  # e.g., "COST", "PERFORMANCE", "QUALITY"
    message: str
    roi_score: float  # Expected ROI 0.0 to 100.0


class RecommendationEngine:
    """Generates actionable recommendations based on telemetry."""

    @classmethod
    def generate_recommendations(cls, tenant_id: str) -> List[Recommendation]:
        """Analyzes recent telemetry and suggests improvements."""
        recommendations = []
        
        # 1. Performance Recommendation Rule
        ocr_times = OptimizationManager.get_metrics(tenant_id, component="OCR", metric_name="execution_time")
        if ocr_times:
            avg_time = sum(m.value for m in ocr_times) / len(ocr_times)
            if avg_time > 5.0:
                recommendations.append(Recommendation(
                    tenant_id=tenant_id,
                    category="PERFORMANCE",
                    message=f"Le modèle OCR actuel est lent (Moy: {avg_time:.2f}s). Passer sur 'ocr-fast' pourrait réduire le temps moyen de 41%.",
                    roi_score=85.0
                ))

        # 2. Cost Recommendation Rule
        llm_costs = OptimizationManager.get_metrics(tenant_id, component="LLM", metric_name="cost")
        if llm_costs:
            total_cost = sum(m.value for m in llm_costs)
            if total_cost > 1000.0:
                recommendations.append(Recommendation(
                    tenant_id=tenant_id,
                    category="COST",
                    message="Coût LLM > $1000. Le Prompt v12 réduit le coût LLM de 32% (Batching).",
                    roi_score=95.0
                ))

        # Sort by ROI
        recommendations.sort(key=lambda x: x.roi_score, reverse=True)
        return recommendations
