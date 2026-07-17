import json
import time
import uuid
from collections.abc import AsyncGenerator

import httpx

from app.config.settings import get_settings
from app.llm.base import BaseLLMProvider
from app.llm.exceptions import ProviderNotConfiguredError, UnsupportedCapabilityError
from app.llm.models import CostMetrics, LLMRequest, LLMResponse, Message, TokenUsage

API_BASE = "https://api.anthropic.com/v1"
ANTHROPIC_VERSION = "2023-06-01"


class AnthropicProvider(BaseLLMProvider):
    name = "Anthropic"
    version = "1.0.0"
    supports_streaming = True
    supports_tools = True
    supports_images = True
    supports_json = True

    def _require_api_key(self) -> str:
        api_key = get_settings().ANTHROPIC_API_KEY
        if not api_key:
            raise ProviderNotConfiguredError(
                "ANTHROPIC_API_KEY is not configured. Set it in the environment/.env "
                "to use the Anthropic provider."
            )
        return api_key

    def _headers(self, api_key: str) -> dict:
        return {
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }

    @staticmethod
    def _split_system_and_messages(messages: list[Message]) -> tuple[str | None, list[dict]]:
        """Anthropic takes system prompts as a top-level field, not a message role."""
        system_parts = [m.content for m in messages if m.role == "system"]
        turns = [
            {"role": m.role, "content": m.content} for m in messages if m.role != "system"
        ]
        system = "\n".join(system_parts) if system_parts else None
        return system, turns

    async def health_check(self) -> bool:
        return get_settings().ANTHROPIC_API_KEY is not None

    async def generate(self, request: LLMRequest) -> LLMResponse:
        api_key = self._require_api_key()
        system, turns = self._split_system_and_messages(request.messages)

        payload = {
            "model": request.model,
            "messages": turns,
            "max_tokens": request.max_tokens or 1024,
            "temperature": request.temperature,
        }
        if system:
            payload["system"] = system
        if request.stop_sequences:
            payload["stop_sequences"] = request.stop_sequences

        start_time = time.time()
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{API_BASE}/messages", headers=self._headers(api_key), json=payload
            )
            response.raise_for_status()
            data = response.json()

        latency_ms = int((time.time() - start_time) * 1000)
        content = "".join(
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        )
        usage = data.get("usage", {})
        prompt_tokens = usage.get("input_tokens", 0)
        completion_tokens = usage.get("output_tokens", 0)

        return LLMResponse(
            id=data.get("id", str(uuid.uuid4())),
            provider_name=self.name,
            model=data.get("model", request.model),
            choices=[Message(role="assistant", content=content)],
            usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            cost=CostMetrics(
                input_cost=self.estimate_cost(prompt_tokens, 0, request.model),
                output_cost=self.estimate_cost(0, completion_tokens, request.model),
                total_cost=self.estimate_cost(prompt_tokens, completion_tokens, request.model),
            ),
            latency_ms=latency_ms,
        )

    async def stream(self, request: LLMRequest) -> AsyncGenerator[str]:
        api_key = self._require_api_key()
        system, turns = self._split_system_and_messages(request.messages)

        payload = {
            "model": request.model,
            "messages": turns,
            "max_tokens": request.max_tokens or 1024,
            "temperature": request.temperature,
            "stream": True,
        }
        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST", f"{API_BASE}/messages", headers=self._headers(api_key), json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    event = json.loads(line[len("data:"):].strip())
                    if event.get("type") == "content_block_delta":
                        text = event.get("delta", {}).get("text")
                        if text:
                            yield text

    def count_tokens(self, text: str) -> int:
        return len(text) // 4

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        if "opus" in model:
            return (prompt_tokens / 1000 * 0.015) + (completion_tokens / 1000 * 0.075)
        return (prompt_tokens / 1000 * 0.003) + (completion_tokens / 1000 * 0.015)

    async def embed(self, texts: list[str], model: str) -> list[list[float]]:
        raise UnsupportedCapabilityError(
            "Anthropic does not offer a public embeddings API. Route embedding "
            "requests to a provider that supports them (e.g. Ollama)."
        )
