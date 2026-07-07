from typing import AsyncGenerator
from app.llm.base import BaseLLMProvider
from app.llm.models import LLMRequest, LLMResponse


class AnthropicProvider(BaseLLMProvider):
    name = "Anthropic"
    version = "1.0.0"
    supports_streaming = True
    supports_tools = True
    supports_images = True
    supports_json = True
    
    async def health_check(self) -> bool:
        return True
        
    async def generate(self, request: LLMRequest) -> LLMResponse:
        raise NotImplementedError("Anthropic API integration pending")
        
    async def stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        raise NotImplementedError("Anthropic API integration pending")
        yield ""
            
    def count_tokens(self, text: str) -> int:
        return len(text) // 4
        
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        if "opus" in model:
            return (prompt_tokens / 1000 * 0.015) + (completion_tokens / 1000 * 0.075)
        return (prompt_tokens / 1000 * 0.003) + (completion_tokens / 1000 * 0.015)

    async def embed(self, texts: list[str], model: str) -> list[list[float]]:
        raise NotImplementedError("Anthropic API integration pending")
