from typing import List
from app.local_ai.ollama.registry import LocalModelRegistry


class EmbeddingManager:
    """Manages generation of text embeddings via local models."""

    @classmethod
    def generate_embeddings(cls, texts: List[str], model_name: str = "nomic-embed") -> List[List[float]]:
        """Simulates generating local embeddings."""
        model = LocalModelRegistry.get_model(model_name)
        if not model or not any("embedding" in exp.lower() for exp in model.expertise):
            raise ValueError(f"Model {model_name} is not suitable for embeddings.")
            
        # Mocking embedding generation (1536 dims simulation)
        return [[0.1, 0.2, 0.3] * 512 for _ in texts]
