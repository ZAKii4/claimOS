import time
import uuid
import json
import httpx
from typing import AsyncGenerator
from app.llm.base import BaseLLMProvider
from app.llm.models import LLMRequest, LLMResponse, Message, TokenUsage, CostMetrics
from app.config.settings import get_settings


class OllamaProvider(BaseLLMProvider):
    name = "Ollama"
    version = "1.0.0"
    supports_streaming = True
    supports_tools = False
    supports_images = False
    supports_json = True
    
    async def health_check(self) -> bool:
        settings = get_settings()
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{settings.OLLAMA_API_URL}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
        
    async def generate(self, request: LLMRequest) -> LLMResponse:
        settings = get_settings()
        model_name = request.model if request.model else settings.OLLAMA_DEFAULT_MODEL
        if model_name == "qwen2.5":
            model_name = "qwen2.5-coder:14b"
        elif "llama" in model_name.lower():
            model_name = "llama3:latest"

        messages_payload = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]

        payload = {
            "model": model_name,
            "messages": messages_payload,
            "stream": False,
            "options": {
                "temperature": request.temperature
            }
        }
        if request.max_tokens:
            payload["options"]["num_predict"] = request.max_tokens
        response_format_type = (request.response_format or {}).get("type")
        if response_format_type in ("json", "json_object"):
            payload["format"] = "json"

        start_time = time.time()
        # Local inference (esp. larger models under contention) is genuinely
        # slower and more variable than a hosted API — 60s was too tight and
        # produced spurious timeouts under load rather than real failures.
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.OLLAMA_API_URL}/api/chat",
                json=payload
            )
            response.raise_for_status()
            res_data = response.json()

        latency_ms = int((time.time() - start_time) * 1000)
        content = res_data.get("message", {}).get("content", "")
        
        prompt_tokens = res_data.get("prompt_eval_count", self.count_tokens("".join([m.content for m in request.messages])))
        completion_tokens = res_data.get("eval_count", self.count_tokens(content))

        return LLMResponse(
            id=str(uuid.uuid4()),
            provider_name=self.name,
            model=model_name,
            choices=[Message(role="assistant", content=content)],
            usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens
            ),
            cost=CostMetrics(
                input_cost=0.0,
                output_cost=0.0,
                total_cost=0.0
            ),
            latency_ms=latency_ms
        )
        
    async def stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        settings = get_settings()
        model_name = request.model if request.model else settings.OLLAMA_DEFAULT_MODEL
        if model_name == "qwen2.5":
            model_name = "qwen2.5-coder:14b"
        elif "llama" in model_name.lower():
            model_name = "llama3:latest"

        messages_payload = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]

        payload = {
            "model": model_name,
            "messages": messages_payload,
            "stream": True,
            "options": {
                "temperature": request.temperature
            }
        }
        if request.max_tokens:
            payload["options"]["num_predict"] = request.max_tokens

        # Local inference (esp. larger models under contention) is genuinely
        # slower and more variable than a hosted API — 60s was too tight and
        # produced spurious timeouts under load rather than real failures.
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{settings.OLLAMA_API_URL}/api/chat",
                json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        chunk = json.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            yield content
            
    def count_tokens(self, text: str) -> int:
        return len(text) // 4
        
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        return 0.0

    async def embed(self, texts: list[str], model: str) -> list[list[float]]:
        settings = get_settings()
        embed_model = "mxbai-embed-large:latest"
        
        embeddings = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for text in texts:
                payload = {
                    "model": embed_model,
                    "prompt": text
                }
                response = await client.post(
                    f"{settings.OLLAMA_API_URL}/api/embeddings",
                    json=payload
                )
                response.raise_for_status()
                res_data = response.json()
                embeddings.append(res_data.get("embedding", []))
        return embeddings

