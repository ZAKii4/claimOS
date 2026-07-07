from typing import Dict, Any, List
from pydantic import BaseModel, Field
import uuid
from datetime import datetime


class TelemetryMetric(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    component: str  # e.g., "OCR", "LLM", "PIPELINE"
    metric_name: str  # e.g., "execution_time", "cost", "error_rate"
    value: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OptimizationManager:
    """Collects and aggregates execution telemetry for continuous optimization."""

    _metrics: List[TelemetryMetric] = []

    @classmethod
    def record_metric(cls, tenant_id: str, component: str, metric_name: str, value: float, metadata: Dict[str, Any] = None) -> TelemetryMetric:
        m = TelemetryMetric(
            tenant_id=tenant_id,
            component=component,
            metric_name=metric_name,
            value=value,
            metadata=metadata or {}
        )
        cls._metrics.append(m)
        return m

    @classmethod
    def get_metrics(cls, tenant_id: str, component: str = None, metric_name: str = None) -> List[TelemetryMetric]:
        res = [m for m in cls._metrics if m.tenant_id == tenant_id]
        if component:
            res = [m for m in res if m.component == component]
        if metric_name:
            res = [m for m in res if m.metric_name == metric_name]
        return res

    @classmethod
    def _clear_all(cls):
        cls._metrics.clear()
