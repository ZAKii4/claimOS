from typing import Dict, Any, List
from pydantic import BaseModel
from app.optimization.ai.selection import ModelSelectionEngine, AIModel


class BenchmarkResult(BaseModel):
    component: str
    leaderboard: List[Dict[str, Any]]


class BenchmarkEngine:
    """Runs automated benchmarks to compare AI models."""

    @classmethod
    def run_benchmark(cls, component: str) -> BenchmarkResult:
        """Simulates a benchmark run across all models for a component."""
        models = ModelSelectionEngine._registry.get(component, [])
        if not models:
            return BenchmarkResult(component=component, leaderboard=[])

        leaderboard = []
        for m in models:
            # Composite score (higher is better): quality / latency penalty / cost penalty
            latency_penalty = max(1, m.avg_latency_ms / 1000)
            cost_penalty = max(1, m.cost_per_unit * 100)
            score = m.quality_score / (latency_penalty * cost_penalty)
            
            leaderboard.append({
                "model": m.name,
                "score": round(score, 2),
                "quality": m.quality_score,
                "latency_ms": m.avg_latency_ms,
                "cost": m.cost_per_unit
            })

        leaderboard.sort(key=lambda x: x["score"], reverse=True)
        return BenchmarkResult(component=component, leaderboard=leaderboard)
