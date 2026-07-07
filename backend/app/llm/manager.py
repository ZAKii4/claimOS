from typing import Dict, Any, List
from app.llm.registry import ProviderRegistry
from app.llm.models import LLMRequest, LLMResponse
from app.llm.cache import LLMCache
from app.llm.telemetry import TelemetryEngine
from app.llm.retry import RetryPolicy
from app.llm.guardrails import GuardrailsEngine


class LLMManager:
    """
    Central Gateway orchestrating all LLM calls.
    Handles caching, routing, telemetry, and retries.
    """
    def __init__(self):
        self.registry = ProviderRegistry()
        self.registry.discover()
        self.cache = LLMCache()
        self.telemetry = TelemetryEngine()
        self.guardrails = GuardrailsEngine()
        
    def _select_provider(self, requested_model: str) -> str:
        """
        Naive routing based on model string.
        In a real scenario, checks cost, latency, health.
        """
        if "gpt" in requested_model.lower():
            return "OpenAI"
        elif "claude" in requested_model.lower():
            return "Anthropic"
        elif "gemini" in requested_model.lower():
            return "Gemini"
        elif "llama" in requested_model.lower():
            return "Ollama"
        return "Mock" # Fallback
        
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Execute the generation with retries, telemetry and cache logic.
        """
        # 1. Cache Check
        cached = self.cache.get(request)
        if cached:
            self.telemetry.log_response(cached, cache_hit=True, retries=0)
            return cached
            
        provider_name = self._select_provider(request.model)
        provider = self.registry.get_provider(provider_name)
        
        if not provider:
            provider = self.registry.get_provider("Mock")
            if not provider:
                raise ValueError(f"No suitable provider found for {request.model}")
                
        # 2. Execute with Retry Policy
        async def _run():
            return await provider.generate(request)
            
        async def _fallback():
            fallback_provider = self.registry.get_provider("Mock")
            return await fallback_provider.generate(request)
            
        response = await RetryPolicy.execute_with_retry(
            func=_run,
            max_retries=3,
            base_delay=1.0,
            fallback_func=_fallback
        )
        
        # 3. Guardrails Check (e.g. valid JSON if requested)
        if request.response_format and request.response_format.get("type") == "json_object":
            try:
                # We expect response choices to be valid json
                raw_content = response.choices[0].content
                self.guardrails.validate_json_output(raw_content)
            except Exception as e:
                # In a real setup, we might retry the generation with an error message
                pass
        
        # 4. Cache & Telemetry
        self.cache.set(request, response)
        self.telemetry.log_response(response, cache_hit=False, retries=0)
        
        return response

    async def embed(self, texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
        """
        Gateway method for embeddings.
        """
        provider_name = self._select_provider(model)
        provider = self.registry.get_provider(provider_name)
        if not provider:
            provider = self.registry.get_provider("Mock")
            
        try:
            return await provider.embed(texts, model)
        except Exception:
            fallback = self.registry.get_provider("Mock")
            return await fallback.embed(texts, model)
