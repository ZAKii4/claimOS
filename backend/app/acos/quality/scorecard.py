from pydantic import BaseModel
from typing import Dict, Any


class ScorecardMetrics(BaseModel):
    faithfulness: float
    grounding: float
    precision: float
    latency_ms: float
    cost_usd: float
    roi_percentage: float
    confidence: float


class EnterpriseScorecard:
    """Aggregates multi-dimensional KPIs into a unified scorecard."""

    @classmethod
    def generate_scorecard(cls, task_id: str, raw_metrics: dict) -> Dict[str, Any]:
        """Simulates generating a comprehensive scorecard."""
        
        # Mocks a structured scorecard based on input
        metrics = ScorecardMetrics(
            faithfulness=raw_metrics.get("faithfulness", 0.95),
            grounding=raw_metrics.get("grounding", 0.98),
            precision=raw_metrics.get("precision", 0.92),
            latency_ms=raw_metrics.get("latency_ms", 1200.0),
            cost_usd=raw_metrics.get("cost_usd", 0.015),
            roi_percentage=raw_metrics.get("roi_percentage", 15.5),
            confidence=raw_metrics.get("confidence", 0.99)
        )
        
        # Determine overall grade
        overall_score = (metrics.faithfulness + metrics.grounding + metrics.precision + metrics.confidence) / 4.0
        
        grade = "A"
        if overall_score < 0.90:
            grade = "B"
        if overall_score < 0.80:
            grade = "C"
        if overall_score < 0.70:
            grade = "F"
            
        return {
            "task_id": task_id,
            "metrics": metrics.model_dump(),
            "overall_score": round(overall_score, 3),
            "grade": grade
        }
