from fastapi import APIRouter
from app.llm.manager import LLMManager
from app.llm.models import LLMRequest
from app.llm.prompts_registry import PromptRegistry

router = APIRouter(prefix="/llm", tags=["Enterprise LLM Gateway"])
manager = LLMManager()
prompts = PromptRegistry()


@router.get("/providers")
def list_providers():
    """List all registered LLM providers."""
    return {
        name: {"version": p.version, "supports_streaming": p.supports_streaming}
        for name, p in manager.registry.get_all().items()
    }


@router.get("/prompts")
def list_prompts():
    """List all registered prompt templates."""
    return [p.model_dump() for p in prompts._prompts.values()]


@router.post("/chat")
async def chat_completion(request: LLMRequest):
    """Generate completion via the Gateway."""
    response = await manager.generate(request)
    return response.model_dump()


@router.get("/telemetry")
def get_telemetry():
    """Get total cost and token usage."""
    return manager.telemetry.get_summary()


@router.get("/cache/stats")
def get_cache_stats():
    """Get LRU Cache statistics."""
    return manager.cache.get_stats()
