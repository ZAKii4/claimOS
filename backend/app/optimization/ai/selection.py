from typing import Dict, Any, List
from pydantic import BaseModel


class AIModel(BaseModel):
    name: str
    component: str  # "OCR", "LLM", "RAG"
    cost_per_unit: float
    avg_latency_ms: float
    quality_score: float  # 0.0 to 100.0


class ModelSelectionEngine:
    """Dynamically routes requests to the optimal AI model based on context."""

    _registry: Dict[str, List[AIModel]] = {
        "LLM": [
            AIModel(name="gpt-4", component="LLM", cost_per_unit=0.03, avg_latency_ms=2500, quality_score=98.0),
            AIModel(name="gpt-3.5", component="LLM", cost_per_unit=0.002, avg_latency_ms=800, quality_score=85.0),
            AIModel(name="local-llama", component="LLM", cost_per_unit=0.0, avg_latency_ms=4000, quality_score=75.0)
        ],
        "OCR": [
            AIModel(name="ocr-high-precision", component="OCR", cost_per_unit=0.01, avg_latency_ms=5000, quality_score=99.0),
            AIModel(name="ocr-fast", component="OCR", cost_per_unit=0.001, avg_latency_ms=500, quality_score=88.0)
        ]
    }

    @classmethod
    def select_model(cls, component: str, context: Dict[str, Any]) -> AIModel:
        """Selects the best model depending on priority constraint."""
        models = cls._registry.get(component, [])
        if not models:
            raise ValueError(f"No models registered for component {component}")

        priority = context.get("priority", "BALANCED")
        
        if priority == "SPEED":
            # Sort by lowest latency
            return sorted(models, key=lambda m: m.avg_latency_ms)[0]
        elif priority == "COST":
            # Sort by lowest cost
            return sorted(models, key=lambda m: m.cost_per_unit)[0]
        elif priority == "QUALITY":
            # Sort by highest quality
            return sorted(models, key=lambda m: m.quality_score, reverse=True)[0]
        else:
            # Balanced: good quality but reasonable cost (simplistic heuristic)
            return sorted(models, key=lambda m: m.quality_score / (m.cost_per_unit + 0.0001), reverse=True)[0]
