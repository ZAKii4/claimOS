from typing import Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class Experiment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    name: str
    parameters: Dict[str, Any]
    metrics: Dict[str, float] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExperimentManager:
    """Tracks AI experiments, hyperparameter tuning, and datasets."""

    _experiments: List[Experiment] = []

    @classmethod
    def log_experiment(cls, tenant_id: str, name: str, parameters: Dict[str, Any]) -> Experiment:
        exp = Experiment(tenant_id=tenant_id, name=name, parameters=parameters)
        cls._experiments.append(exp)
        return exp

    @classmethod
    def log_metrics(cls, experiment_id: str, metrics: Dict[str, float]):
        for exp in cls._experiments:
            if exp.id == experiment_id:
                exp.metrics.update(metrics)
                break

    @classmethod
    def get_experiments(cls, tenant_id: str, name: str = None) -> List[Experiment]:
        res = [e for e in cls._experiments if e.tenant_id == tenant_id]
        if name:
            res = [e for e in res if e.name == name]
        return res

    @classmethod
    def _clear_all(cls):
        cls._experiments.clear()
