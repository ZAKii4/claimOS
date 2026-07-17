from typing import List
from app.llm.manager import DEFAULT_EMBEDDING_MODEL, LLMManager


class EmbeddingsEngine:
    """Wrapper to generate embeddings using the central LLMGateway."""

    def __init__(self, llm_manager: LLMManager):
        self.llm = llm_manager

    async def embed_texts(self, texts: List[str], model: str = DEFAULT_EMBEDDING_MODEL) -> List[List[float]]:
        """Fetch embeddings for a batch of texts."""
        if not texts:
            return []
        vectors = await self.llm.embed(texts, model=model)
        return vectors

    async def embed_query(self, query: str, model: str = DEFAULT_EMBEDDING_MODEL) -> List[float]:
        """Fetch embedding for a single query."""
        vectors = await self.llm.embed([query], model=model)
        return vectors[0] if vectors else []
