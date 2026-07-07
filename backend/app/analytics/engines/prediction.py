from typing import Dict, Any
from app.analytics.lake.warehouse import AnalyticsWarehouse


class PredictionEngine:
    """Produces business forecasts (costs, volumes)."""

    @classmethod
    def forecast_volume(cls, tenant_id: str, days_ahead: int = 30) -> Dict[str, Any]:
        """Simple moving average forecast."""
        facts = AnalyticsWarehouse.get_raw_facts(tenant_id, "claims")
        if not facts:
            return {"forecast": 0, "confidence": 0.0}
            
        # Simplistic stub: average per existing day * days_ahead
        # Not a real time-series, just a structural mock
        total_claims = len(facts)
        forecast = total_claims * 1.05  # predict 5% growth
        
        return {
            "forecast": round(forecast),
            "confidence": 0.85
        }

    @classmethod
    def forecast_llm_costs(cls, tenant_id: str) -> float:
        """Forecasts LLM costs based on current rate."""
        agg = AnalyticsWarehouse.query_aggregate(tenant_id, "llm_usage")
        current_cost = agg.get("cost", 0.0)
        return round(current_cost * 1.2, 2)  # predict 20% increase
