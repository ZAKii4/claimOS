
from app.llm.manager import DEFAULT_EMBEDDING_MODEL, LLMManager


class SimilarityEngine:
    """Generates real embeddings via the LLM gateway (Ollama's mxbai-embed-large by default)."""

    def __init__(self, llm_manager: LLMManager | None = None):
        self.llm = llm_manager or LLMManager()

    async def generate_embedding(self, text: str) -> list[float]:
        vectors = await self.llm.embed([text], model=DEFAULT_EMBEDDING_MODEL)
        return vectors[0] if vectors else []


similarity_engine = SimilarityEngine()
