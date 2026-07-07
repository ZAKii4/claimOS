from typing import AsyncGenerator
from app.llm.base import BaseLLMProvider
from app.llm.models import LLMRequest, LLMResponse


class OllamaProvider(BaseLLMProvider):
    name = "Ollama"
    version = "1.0.0"
    supports_streaming = True
    supports_tools = False
    supports_images = False
    supports_json = True
    
    async def health_check(self) -> bool:
        return True
        
    async def generate(self, request: LLMRequest) -> LLMResponse:
        raise NotImplementedError("Ollama API integration pending")
        
    async def stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        raise NotImplementedError("Ollama API integration pending")
        yield ""
            
    def count_tokens(self, text: str) -> int:
        return len(text) // 4
        
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        return 0.0

    async def embed(self, texts: list[str], model: str) -> list[list[float]]:
        raise NotImplementedError("Ollama API integration pending")
