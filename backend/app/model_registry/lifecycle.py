from typing import Dict, Any
from app.model_registry.registry import ModelRegistry


class LifecycleManager:
    """Manages model transitions (Training -> Staging -> Production)."""

    @classmethod
    def transition_model(cls, model_id: str, new_status: str) -> bool:
        model = ModelRegistry.get_model(model_id)
        if not model:
            return False
        
        # In a real scenario, this would enforce state machine transitions
        model["status"] = new_status
        return True
