import logging

from app.llm.cache import LLMCache
from app.llm.exceptions import LLMProviderUnavailableError
from app.llm.guardrails import GuardrailsEngine
from app.llm.models import LLMRequest, LLMResponse
from app.llm.registry import ProviderRegistry
from app.llm.retry import RetryPolicy
from app.llm.telemetry import TelemetryEngine

logger = logging.getLogger("claimOS.llm")

# Maps a substring found in a requested model name to the provider that serves
# it. Checked in order; the first match wins. Anything unrecognized routes to
# Ollama — the platform's local, self-hosted, always-configured provider —
# rather than to a fabricated response.
MODEL_PROVIDER_PREFIXES: list[tuple[str, str]] = [
    ("gpt", "OpenAI"),
    ("claude", "Anthropic"),
    ("gemini", "Gemini"),
    ("llama", "Ollama"),
    ("qwen", "Ollama"),
    ("deepseek", "Ollama"),
    ("mxbai", "Ollama"),
    ("nomic", "Ollama"),
]

DEFAULT_EMBEDDING_MODEL = "mxbai-embed-large"


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
        """Routes a model name to the provider that serves it."""
        model_lower = (requested_model or "").lower()
        for prefix, provider_name in MODEL_PROVIDER_PREFIXES:
            if prefix in model_lower:
                return provider_name
        return "Ollama"

    def _get_provider(self, provider_name: str, requested_model: str):
        provider = self.registry.get_provider(provider_name)
        if not provider:
            raise LLMProviderUnavailableError(
                f"No '{provider_name}' provider is registered "
                f"(requested model: '{requested_model}')."
            )
        return provider

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Execute the generation with retries, telemetry and cache logic.

        Raises LLMProviderUnavailableError (or whatever the provider raises,
        e.g. ProviderNotConfiguredError) if no real provider can service the
        request — this call never silently substitutes a fabricated response.
        """
        cached = self.cache.get(request)
        if cached:
            self.telemetry.log_response(cached, cache_hit=True, retries=0)
            return cached

        provider_name = self._select_provider(request.model)
        provider = self._get_provider(provider_name, request.model)

        if not await provider.health_check():
            raise LLMProviderUnavailableError(
                f"Provider '{provider_name}' failed its health check "
                f"(requested model: '{request.model}'). Is it configured/reachable?"
            )

        async def _run():
            return await provider.generate(request)

        response = await RetryPolicy.execute_with_retry(
            func=_run,
            max_retries=3,
            base_delay=1.0,
        )

        if request.response_format and request.response_format.get("type") == "json_object":
            try:
                raw_content = response.choices[0].content
                self.guardrails.validate_json_output(raw_content)
            except Exception as e:
                logger.warning("Response failed JSON guardrail validation: %s", e)

        self.cache.set(request, response)
        self.telemetry.log_response(response, cache_hit=False, retries=0)

        return response

    async def embed(
        self, texts: list[str], model: str = DEFAULT_EMBEDDING_MODEL
    ) -> list[list[float]]:
        """
        Gateway method for embeddings.

        Raises LLMProviderUnavailableError if no real provider can service the
        request — no fabricated/random vectors are ever returned.
        """
        if not texts:
            return []

        provider_name = self._select_provider(model)
        provider = self._get_provider(provider_name, model)

        if not await provider.health_check():
            raise LLMProviderUnavailableError(
                f"Provider '{provider_name}' failed its health check "
                f"(requested embedding model: '{model}'). Is it configured/reachable?"
            )

        return await provider.embed(texts, model)
