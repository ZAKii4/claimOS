from typing import Dict, Any, List
from pydantic import BaseModel
from app.optimization.core.manager import OptimizationManager


class CapacityForecast(BaseModel):
    resource: str
    current_usage: float
    forecasted_usage: float
    saturation_risk: str
    recommendation: str


class CapacityPlanningEngine:
    """Predicts future resource requirements before saturation."""

    @classmethod
    def forecast_capacity(cls, tenant_id: str) -> List[CapacityForecast]:
        forecasts = []
        
        cpu_metrics = OptimizationManager.get_metrics(tenant_id, component="PIPELINE", metric_name="cpu")
        if cpu_metrics:
            avg_cpu = sum(m.value for m in cpu_metrics) / len(cpu_metrics)
            forecast_cpu = avg_cpu * 1.2  # 20% predicted growth
            
            risk = "HIGH" if forecast_cpu > 80.0 else ("MEDIUM" if forecast_cpu > 60.0 else "LOW")
            rec = "Scale out workers (add +2 nodes)" if risk == "HIGH" else "Monitor"
            
            forecasts.append(CapacityForecast(
                resource="CPU",
                current_usage=round(avg_cpu, 2),
                forecasted_usage=round(forecast_cpu, 2),
                saturation_risk=risk,
                recommendation=rec
            ))

        llm_calls = OptimizationManager.get_metrics(tenant_id, component="LLM", metric_name="calls")
        if llm_calls:
            total_calls = sum(m.value for m in llm_calls)
            forecast_calls = total_calls * 1.5
            
            risk = "HIGH" if forecast_calls > 10000 else "LOW"
            rec = "Request LLM quota increase" if risk == "HIGH" else "Sufficient quota"
            
            forecasts.append(CapacityForecast(
                resource="LLM Quota",
                current_usage=total_calls,
                forecasted_usage=forecast_calls,
                saturation_risk=risk,
                recommendation=rec
            ))

        return forecasts
