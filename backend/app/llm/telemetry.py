from typing import Dict, Any, List
from app.llm.models import LLMResponse


class TelemetryEngine:
    """Tracks latency, cost, and usage metrics across the LLM Gateway."""
    
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        self.total_cost = 0.0
        self.total_tokens = 0
        
    def log_response(self, response: LLMResponse, cache_hit: bool = False, retries: int = 0):
        entry = {
            "id": response.id,
            "provider": response.provider_name,
            "model": response.model,
            "latency_ms": response.latency_ms,
            "tokens": response.usage.total_tokens,
            "cost": response.cost.total_cost,
            "cache_hit": cache_hit,
            "retries": retries,
            "timestamp": response.created_at.isoformat()
        }
        self.history.append(entry)
        
        self.total_cost += response.cost.total_cost
        self.total_tokens += response.usage.total_tokens
        
    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_calls": len(self.history),
            "total_cost": self.total_cost,
            "total_tokens": self.total_tokens,
            "avg_latency": sum(h["latency_ms"] for h in self.history) / len(self.history) if self.history else 0
        }
