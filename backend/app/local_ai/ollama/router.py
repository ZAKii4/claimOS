from typing import Optional, Dict
from app.local_ai.ollama.registry import LocalModelRegistry, LocalModelMeta


class ModelRoutingEngine:
    """Intelligently routes tasks to the best local model."""

    _task_routes: Dict[str, str] = {
        "OCR Cleaning": "phi-4",
        "Classification": "gemma-3",
        "Entity Extraction": "qwen-2.5",
        "Fraud Analysis": "deepseek-r1",
        "Legal Analysis": "granite",
        "Report Generation": "mistral",
        "Chat Assistant": "llama-3.1",
        "Embeddings": "nomic-embed"
    }

    @classmethod
    def route_task(cls, task_type: str) -> Optional[LocalModelMeta]:
        """Returns the appropriate model for the task. Default to llama-3.1 if unknown."""
        model_name = cls._task_routes.get(task_type, "llama-3.1")
        return LocalModelRegistry.get_model(model_name)
