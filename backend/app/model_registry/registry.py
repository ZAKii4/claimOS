from typing import Dict, Any, List
import uuid
import time


class ModelRegistry:
    """Enterprise Model Registry: The single source of truth for all AI models."""

    _models: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register_model(cls, name: str, version: str, provider: str, m_type: str) -> Dict[str, Any]:
        model_id = str(uuid.uuid4())
        model = {
            "id": model_id,
            "name": name,
            "version": version,
            "provider": provider,
            "type": m_type,
            "domain": "Claims",
            "license": "Commercial",
            "training_date": time.time(),
            "status": "DRAFT",
            "owner": "AI Governance Team"
        }
        cls._models[model_id] = model
        return model

    @classmethod
    def get_model(cls, model_id: str) -> Dict[str, Any]:
        return cls._models.get(model_id, {})

    @classmethod
    def get_all_models(cls) -> List[Dict[str, Any]]:
        return list(cls._models.values())

    @classmethod
    def _reset(cls):
        cls._models.clear()
