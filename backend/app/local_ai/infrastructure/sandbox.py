from typing import Dict, Any
from pydantic import BaseModel, Field
import uuid
import time
from app.local_ai.ollama.registry import LocalModelRegistry


class SandboxExperiment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    model_name: str
    prompt: str
    latency_ms: float = 0.0
    quality_score: float = 0.0
    status: str = "PENDING"


class LocalAISandbox:
    """Isolated environment to test new models without impacting production."""

    _experiments: Dict[str, SandboxExperiment] = {}

    @classmethod
    def run_experiment(cls, model_name: str, prompt: str) -> SandboxExperiment:
        """Simulates running a prompt against a specific local model."""
        exp = SandboxExperiment(model_name=model_name, prompt=prompt)
        cls._experiments[exp.id] = exp
        
        model = LocalModelRegistry.get_model(model_name)
        if not model:
            exp.status = "FAILED - MODEL NOT FOUND"
            return exp
            
        # Simulate execution
        exp.latency_ms = model.avg_throughput_tps * 10.0  # mock latency
        exp.quality_score = 85.0 if model.quality_level == "HIGH" else 70.0
        exp.status = "COMPLETED"
        return exp

    @classmethod
    def get_experiment(cls, exp_id: str) -> SandboxExperiment:
        return cls._experiments.get(exp_id)
