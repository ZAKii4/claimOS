import json
import time
import uuid
from collections.abc import AsyncGenerator

import httpx

from app.config.settings import get_settings
from app.llm.base import BaseLLMProvider
from app.llm.exceptions import ProviderNotConfiguredError
from app.llm.models import CostMetrics, LLMRequest, LLMResponse, Message, TokenUsage

API_BASE = "https://generativelanguage.googleapis.com/v1beta"
_ROLE_MAP = {"assistant": "model", "user": "user"}


class GeminiProvider(BaseLLMProvider):
    name = "Gemini"
    version = "1.0.0"
    supports_streaming = True
    supports_tools = True
    supports_images = True
    supports_json = True

    def _require_api_key(self) -> str:
        api_key = get_settings().GEMINI_API_KEY
        if not api_key:
            raise ProviderNotConfiguredError(
                "GEMINI_API_KEY is not configured. Set it in the environment/.env "
                "to use the Gemini provider."
            )
        return api_key

    @staticmethod
    def _build_contents_and_system(messages: list[Message]) -> tuple[list[dict], str | None]:
        system_parts = [m.content for m in messages if m.role == "system"]
        contents = [
            {"role": _ROLE_MAP.get(m.role, "user"), "parts": [{"text": m.content}]}
            for m in messages
            if m.role != "system"
        ]
        system = "\n".join(system_parts) if system_parts else None
        return contents, system

    async def health_check(self) -> bool:
        return get_settings().GEMINI_API_KEY is not None

    async def generate(self, request: LLMRequest) -> LLMResponse:
        api_key = self._require_api_key()
        contents, system = self._build_contents_and_system(request.messages)

        payload = {
            "contents": contents,
            "generationConfig": {"temperature": request.temperature},
        }
        if request.max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = request.max_tokens
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}

        start_time = time.time()
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{API_BASE}/models/{request.model}:generateContent",
                params={"key": api_key},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        latency_ms = int((time.time() - start_time) * 1000)
        candidate = data["candidates"][0]
        content = "".join(
            part.get("text", "") for part in candidate.get("content", {}).get("parts", [])
        )
        usage = data.get("usageMetadata", {})
        prompt_tokens = usage.get("promptTokenCount", 0)
        completion_tokens = usage.get("candidatesTokenCount", 0)

        return LLMResponse(
            id=str(uuid.uuid4()),
            provider_name=self.name,
            model=request.model,
            choices=[Message(role="assistant", content=content)],
            usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=usage.get("totalTokenCount", prompt_tokens + completion_tokens),
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
        contents, system = self._build_contents_and_system(request.messages)

        payload = {
            "contents": contents,
            "generationConfig": {"temperature": request.temperature},
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{API_BASE}/models/{request.model}:streamGenerateContent",
                params={"key": api_key, "alt": "sse"},
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    chunk = json.loads(line[len("data:"):].strip())
                    for part in chunk["candidates"][0].get("content", {}).get("parts", []):
                        text = part.get("text")
                        if text:
                            yield text

    def count_tokens(self, text: str) -> int:
        return len(text) // 4

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        if "pro" in model:
            return (prompt_tokens / 1000 * 0.00125) + (completion_tokens / 1000 * 0.00375)
        return (prompt_tokens / 1000 * 0.000125) + (completion_tokens / 1000 * 0.000375)

    async def embed(self, texts: list[str], model: str) -> list[list[float]]:
        api_key = self._require_api_key()
        embed_model = model if "embedding" in model.lower() else "text-embedding-004"

        embeddings = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for text in texts:
                response = await client.post(
                    f"{API_BASE}/models/{embed_model}:embedContent",
                    params={"key": api_key},
                    json={"content": {"parts": [{"text": text}]}},
                )
                response.raise_for_status()
                data = response.json()
                embeddings.append(data.get("embedding", {}).get("values", []))
        return embeddings
