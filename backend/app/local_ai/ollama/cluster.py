from typing import List, Dict, Any
from app.local_ai.ollama.registry import LocalModelRegistry


class OllamaClusterManager:
    """Simulates communication with an Ollama cluster to discover and load models."""

    _active_nodes = ["node-1", "node-2"]

    @classmethod
    def discover_models(cls) -> List[str]:
        """Simulates `ollama list` across the cluster."""
        return [m.name for m in LocalModelRegistry.list_models()]

    @classmethod
    def load_model(cls, name: str) -> bool:
        """Simulates loading a model into memory."""
        model = LocalModelRegistry.get_model(name)
        if not model:
            return False
        # Mock logic: assuming success
        LocalModelRegistry.update_status(name, True)
        return True

    @classmethod
    def unload_model(cls, name: str) -> bool:
        """Simulates unloading a model to free VRAM."""
        model = LocalModelRegistry.get_model(name)
        if not model:
            return False
        LocalModelRegistry.update_status(name, False)
        return True

    @classmethod
    def get_cluster_status(cls) -> Dict[str, Any]:
        loaded_models = [m.name for m in LocalModelRegistry.list_models() if m.is_loaded]
        return {
            "status": "ONLINE",
            "nodes": len(cls._active_nodes),
            "loaded_models": loaded_models
        }
