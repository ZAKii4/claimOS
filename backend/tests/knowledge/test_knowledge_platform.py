import pytest
import pytest_asyncio
import networkx as nx

from app.vector.repository import vector_repo
from app.vector.semantic_cache import semantic_cache
from app.vector.similarity_engine import similarity_engine
from app.graph.neo4j_repository import graph_repo
from app.graph.entity_resolver import entity_resolver
from app.graph.fraud_network import fraud_analyzer
from app.knowledge.hybrid_rag import hybrid_rag
from app.knowledge.context_compression import context_compression
from app.knowledge.evidence_ranking import evidence_ranking
from app.core.database import get_session_factory
from app.models.knowledge import TenantEmbedding

TEST_TENANT = "T1"
requires_ollama = pytest.mark.requires_ollama


@pytest_asyncio.fixture(autouse=True)
async def reset_state():
    def _clear_tenant_embeddings():
        Session = get_session_factory()
        db = Session()
        try:
            db.query(TenantEmbedding).filter(
                TenantEmbedding.tenant_id == TEST_TENANT
            ).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()

    semantic_cache._cache = []
    graph_repo._graph = nx.MultiDiGraph()
    _clear_tenant_embeddings()
    yield
    semantic_cache._cache = []
    graph_repo._graph = nx.MultiDiGraph()
    _clear_tenant_embeddings()


@requires_ollama
@pytest.mark.asyncio
async def test_vector_search():
    tenant = TEST_TENANT
    # Generate real embeddings (Ollama's mxbai-embed-large)
    vec1 = await similarity_engine.generate_embedding("insurance policy details")
    vec2 = await similarity_engine.generate_embedding("irrelevant text about cars")

    await vector_repo.add_embedding(tenant, "doc1", 0, "insurance policy details", vec1)
    await vector_repo.add_embedding(tenant, "doc2", 0, "irrelevant text about cars", vec2)

    # Search with identical text
    results = await vector_repo.search_similar(tenant, vec1, top_k=1)
    assert len(results) == 1
    assert results[0]["document_id"] == "doc1"
    assert results[0]["score"] > 0.99


@requires_ollama
@pytest.mark.asyncio
async def test_semantic_cache():
    q_emb = await similarity_engine.generate_embedding("What is my deductible?")
    # Cache miss
    ans = await semantic_cache.get_cached_response(q_emb)
    assert ans is None

    # Set cache
    await semantic_cache.set_cache(q_emb, "Your deductible is 500 euros.")

    # Cache hit
    ans2 = await semantic_cache.get_cached_response(q_emb)
    assert ans2 == "Your deductible is 500 euros."


@pytest.mark.asyncio
async def test_entity_resolution():
    existing = [
        {"id": "E1", "name": "John Doe", "email": "john@example.com"},
        {"id": "E2", "name": "Jane Doe", "phone": "123456789"}
    ]

    new_entity_1 = {"name": "J. Doe", "email": "john@example.com"}
    resolved_id = await entity_resolver.resolve_entities(new_entity_1, existing)
    assert resolved_id == "E1"

    new_entity_2 = {"name": "Bob", "email": "bob@example.com"}
    resolved_id2 = await entity_resolver.resolve_entities(new_entity_2, existing)
    assert resolved_id2 is None


@pytest.mark.asyncio
async def test_fraud_network():
    # Create a ring of 3 entities
    await graph_repo.create_node("Person", {"id": "P1"})
    await graph_repo.create_node("Person", {"id": "P2"})
    await graph_repo.create_node("Person", {"id": "P3"})
    await graph_repo.create_node("Person", {"id": "P4"}) # isolated

    await graph_repo.create_relationship("P1", "P2", "KNOWS")
    await graph_repo.create_relationship("P2", "P3", "KNOWS")
    await graph_repo.create_relationship("P3", "P1", "KNOWS")

    rings = await fraud_analyzer.detect_fraud_rings()
    assert len(rings) == 1
    assert rings[0]["size"] == 3
    assert set(rings[0]["entities"]) == {"P1", "P2", "P3"}


@requires_ollama
@pytest.mark.asyncio
async def test_hybrid_rag_retrieval():
    tenant = TEST_TENANT
    vec1 = await similarity_engine.generate_embedding("policy coverage")
    await vector_repo.add_embedding(tenant, "doc1", 0, "policy coverage is global", vec1)

    await graph_repo.create_node("Claim", {"id": "C1"})

    result = await hybrid_rag.retrieve_context(tenant, "policy coverage")
    assert result["vector_sources"] == 1
    assert result["graph_sources"] == 1
    assert "policy coverage is global" in result["context"]


@requires_ollama
@pytest.mark.asyncio
async def test_hybrid_rag_generate_answer_is_grounded_and_real():
    """
    The final answer must come from a real LLM call grounded in the retrieved
    context — not a fabricated f-string template counting sources.
    """
    tenant = TEST_TENANT
    vec1 = await similarity_engine.generate_embedding("policy coverage")
    await vector_repo.add_embedding(
        tenant, "doc1", 0, "This insurance policy covers water damage only.", vec1
    )

    result = await hybrid_rag.generate_answer(tenant, "What does my policy cover?")
    assert result["vector_sources"] >= 1
    answer = result["answer"].lower()
    assert answer.strip() != ""
    # A grounded answer about water-damage coverage should mention water damage,
    # not just report source counts.
    assert "water" in answer


@pytest.mark.asyncio
async def test_evidence_ranking():
    evidences = [
        {"score": 0.5, "metadata": {"source": "unofficial", "is_verified": False}},
        {"score": 0.5, "metadata": {"source": "official", "is_verified": True}}
    ]

    ranked = await evidence_ranking.rank_evidence(evidences)
    # The verified official one should have a higher score
    assert ranked[0]["metadata"]["source"] == "official"
    assert ranked[0]["final_score"] > 0.5
    assert ranked[1]["final_score"] == 0.5


@pytest.mark.asyncio
async def test_context_compression():
    parts = ["A" * 1000, "B" * 2000, "C" * 10000]
    # Token approx 1 = 4 chars
    # parts token size: 250, 500, 2500
    # max tokens: 2000
    compressed = await context_compression.compress(parts, max_tokens=2000)
    # Should include A and B (750 tokens total), but not C
    assert "A" * 1000 in compressed
    assert "B" * 2000 in compressed
    assert "C" * 10000 not in compressed
