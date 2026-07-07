from typing import Dict, Any, List
from pydantic import BaseModel
from app.optimization.core.manager import OptimizationManager


class CostOptimization(BaseModel):
    category: str
    description: str
    estimated_savings_percent: float
    impact: str
    risk: str


class CostOptimizationEngine:
    """Finds financial optimizations based on telemetry."""

    @classmethod
    def analyze_costs(cls, tenant_id: str) -> List[CostOptimization]:
        optimizations = []
        
        llm_costs = OptimizationManager.get_metrics(tenant_id, component="LLM", metric_name="cost")
        total_llm = sum(m.value for m in llm_costs)
        
        # 1. Cache rule
        if total_llm > 500:
            optimizations.append(CostOptimization(
                category="CACHE",
                description="High LLM costs detected. Enabling semantic cache could save costs on redundant queries.",
                estimated_savings_percent=25.0,
                impact="HIGH",
                risk="LOW"
            ))

        # 2. Model downgrade rule
        if total_llm > 2000:
            optimizations.append(CostOptimization(
                category="MODEL",
                description="Very high LLM costs. Consider routing low-priority tasks to 'gpt-3.5' or 'local-llama'.",
                estimated_savings_percent=60.0,
                impact="HIGH",
                risk="MEDIUM"
            ))

        # 3. Batching rule
        ocr_ops = len(OptimizationManager.get_metrics(tenant_id, component="OCR", metric_name="execution_time"))
        if ocr_ops > 1000:
            optimizations.append(CostOptimization(
                category="BATCHING",
                description="High volume of OCR operations. Implementing batching can reduce per-unit cost.",
                estimated_savings_percent=15.0,
                impact="MEDIUM",
                risk="LOW"
            ))

        optimizations.sort(key=lambda x: x.estimated_savings_percent, reverse=True)
        return optimizations
