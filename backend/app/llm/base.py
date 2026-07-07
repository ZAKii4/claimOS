from abc import ABC, abstractmethod
from typing import AsyncGenerator
from app.llm.models import LLMRequest, LLMResponse


class BaseLLMProvider(ABC):
    name: str
    version: str
    supports_streaming: bool
    supports_tools: bool
    supports_images: bool
    supports_json: bool
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Verifies connection and credentials."""
        pass
        
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Standard full generation."""
        pass
        
    @abstractmethod
    async def stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Streaming generation yielding tokens."""
        pass
        
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens offline if possible."""
        pass
        
    @abstractmethod
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        """Estimate the cost of a generation."""
        pass

    @abstractmethod
    async def embed(self, texts: list[str], model: str) -> list[list[float]]:
        """Generate vector embeddings for texts."""
        pass
