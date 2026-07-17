from typing import Any

from fastapi import APIRouter, HTTPException

from app.graph.fraud_network import fraud_analyzer
from app.knowledge.hybrid_rag import hybrid_rag
from app.vector.semantic_cache import semantic_cache
from app.vector.similarity_engine import similarity_engine

router = APIRouter(prefix="/knowledge", tags=["Knowledge & Hybrid RAG"])

@router.post("/hybrid-search")
async def hybrid_search(payload: dict[str, Any]):
    tenant_id = payload.get("tenant_id", "default")
    query = payload.get("query", "")

    if not query:
        raise HTTPException(status_code=400, detail="Query is required")

    # Check cache first
    query_emb = await similarity_engine.generate_embedding(query)
    cached = await semantic_cache.get_cached_response(query_emb)
    if cached:
        return {
            "status": "cache_hit",
            "response": cached,
            "context_used": {"query": query, "vector_sources": 0, "graph_sources": 0},
        }

    # Retrieve Hybrid Context and generate a real, grounded LLM answer
    result = await hybrid_rag.generate_answer(tenant_id, query)
    response = result["answer"]

    # Save to cache
    await semantic_cache.set_cache(query_emb, response)

    return {
        "status": "generated",
        "response": response,
        "context_used": {k: v for k, v in result.items() if k != "answer"},
    }

@router.get("/graph/fraud-rings")
async def get_fraud_rings():
    rings = await fraud_analyzer.detect_fraud_rings()
    return {"fraud_rings": rings, "count": len(rings)}
