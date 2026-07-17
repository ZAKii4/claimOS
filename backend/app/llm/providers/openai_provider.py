import json
import time
import uuid
from collections.abc import AsyncGenerator

import httpx

from app.config.settings import get_settings
from app.llm.base import BaseLLMProvider
from app.llm.exceptions import ProviderNotConfiguredError
from app.llm.models import CostMetrics, LLMRequest, LLMResponse, Message, TokenUsage

API_BASE = "https://api.openai.com/v1"


class OpenAIProvider(BaseLLMProvider):
    name = "OpenAI"
    version = "1.0.0"
    supports_streaming = True
    supports_tools = True
    supports_images = True
    supports_json = True

    def _require_api_key(self) -> str:
        api_key = get_settings().OPENAI_API_KEY
        if not api_key:
            raise ProviderNotConfiguredError(
                "OPENAI_API_KEY is not configured. Set it in the environment/.env "
                "to use the OpenAI provider."
            )
        return api_key

    async def health_check(self) -> bool:
        api_key = get_settings().OPENAI_API_KEY
        if not api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{API_BASE}/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                return response.status_code == 200
        except Exception:
            return False

    async def generate(self, request: LLMRequest) -> LLMResponse:
        api_key = self._require_api_key()

        payload = {
            "model": request.model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
        }
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens
        if request.stop_sequences:
            payload["stop"] = request.stop_sequences
        if request.response_format and request.response_format.get("type") == "json_object":
            payload["response_format"] = {"type": "json_object"}

        start_time = time.time()
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{API_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        latency_ms = int((time.time() - start_time) * 1000)
        choice = data["choices"][0]["message"]
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)

        return LLMResponse(
            id=data.get("id", str(uuid.uuid4())),
            provider_name=self.name,
            model=data.get("model", request.model),
            choices=[
                Message(role=choice.get("role", "assistant"), content=choice.get("content", ""))
            ],
            usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=usage.get("total_tokens", prompt_tokens + completion_tokens),
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

        payload = {
            "model": request.model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
            "stream": True,
        }
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{API_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data_str = line[len("data:"):].strip()
                    if data_str == "[DONE]":
                        break
                    chunk = json.loads(data_str)
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        yield content

    def count_tokens(self, text: str) -> int:
        return len(text) // 4

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        if "gpt-4" in model:
            return (prompt_tokens / 1000 * 0.03) + (completion_tokens / 1000 * 0.06)
        return (prompt_tokens / 1000 * 0.001) + (completion_tokens / 1000 * 0.002)

    async def embed(self, texts: list[str], model: str) -> list[list[float]]:
        api_key = self._require_api_key()
        embed_model = model if "embedding" in model.lower() else "text-embedding-3-small"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_BASE}/embeddings",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": embed_model, "input": texts},
            )
            response.raise_for_status()
            data = response.json()

        return [item["embedding"] for item in data["data"]]
