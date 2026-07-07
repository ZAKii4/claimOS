import uuid
import asyncio
from typing import AsyncGenerator
from app.llm.base import BaseLLMProvider
from app.llm.models import LLMRequest, LLMResponse, Message, TokenUsage, CostMetrics


class MockProvider(BaseLLMProvider):
    name = "Mock"
    version = "1.0.0"
    supports_streaming = True
    supports_tools = True
    supports_images = False
    supports_json = True
    
    async def health_check(self) -> bool:
        return True
        
    async def generate(self, request: LLMRequest) -> LLMResponse:
        # Simulate network latency
        await asyncio.sleep(0.5)
        
        prompt_tokens = self.count_tokens("".join([m.content for m in request.messages]))
        completion_tokens = 50
        
        return LLMResponse(
            id=str(uuid.uuid4()),
            provider_name=self.name,
            model=request.model,
            choices=[Message(role="assistant", content="This is a mocked response.")],
            usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens
            ),
            cost=CostMetrics(
                input_cost=self.estimate_cost(prompt_tokens, 0, request.model),
                output_cost=self.estimate_cost(0, completion_tokens, request.model),
                total_cost=self.estimate_cost(prompt_tokens, completion_tokens, request.model)
            ),
            latency_ms=500
        )
        
    async def stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        words = ["This ", "is ", "a ", "mocked ", "streamed ", "response."]
        for word in words:
            await asyncio.sleep(0.1)
            yield word
            
    def count_tokens(self, text: str) -> int:
        # Extremely rough approximation: 1 token ~= 4 chars
        return len(text) // 4
        
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        return 0.0

    async def embed(self, texts: list[str], model: str) -> list[list[float]]:
        # Mock 1536-dimensional embeddings (e.g., openai size)
        import random
        await asyncio.sleep(0.1)
        return [[random.random() for _ in range(1536)] for _ in texts]
