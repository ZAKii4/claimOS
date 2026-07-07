import pytest
import asyncio
from app.knowledge.manager import KnowledgeManager
from app.knowledge.chunking import ChunkingEngine
from app.knowledge.vector_store import MockVectorStore
from app.knowledge.keyword_index import BM25Index
from app.knowledge.reranker import Reranker
from app.knowledge.citation import GroundingEngine
from app.llm.manager import LLMManager
from app.knowledge.models import KnowledgeChunk, SearchResult


def test_chunking():
    text = "A" * 1000
    chunks = ChunkingEngine.fixed_size_chunking("doc1", text, chunk_size=500, overlap=50)
    assert len(chunks) == 3
    assert len(chunks[0].content) == 500


def test_vector_store():
    store = MockVectorStore()
    c1 = KnowledgeChunk(id="1", document_id="doc1", content="A", position_index=0, vector=[1.0, 0.0, 0.0])
    c2 = KnowledgeChunk(id="2", document_id="doc1", content="B", position_index=1, vector=[0.0, 1.0, 0.0])
    store.add_chunks([c1, c2])
    
    # Query matching c2
    results = store.search(query_vector=[0.0, 1.0, 0.0], top_k=1)
    assert results[0].chunk.id == "2"


def test_bm25_index():
    bm25 = BM25Index()
    c1 = KnowledgeChunk(id="1", document_id="doc1", content="The quick brown fox", position_index=0)
    c2 = KnowledgeChunk(id="2", document_id="doc1", content="Jumped over the lazy dog", position_index=1)
    bm25.add_chunks([c1, c2])
    
    results = bm25.search("fox", top_k=1)
    assert len(results) == 1
    assert results[0].chunk.id == "1"


def test_reranker_rrf():
    c1 = KnowledgeChunk(id="1", document_id="d1", content="A", position_index=0)
    c2 = KnowledgeChunk(id="2", document_id="d1", content="B", position_index=1)
    
    # c1 is rank 1 in vector, c2 is rank 1 in bm25
    v_res = [SearchResult(chunk=c1, score=1.0, vector_score=1.0)]
    b_res = [SearchResult(chunk=c2, score=1.0, bm25_score=1.0), SearchResult(chunk=c1, score=0.5, bm25_score=0.5)]
    
    final = Reranker.rrf(v_res, b_res, k=60)
    # c1 appears twice, so its combined RRF score should be higher than c2
    assert final[0].chunk.id == "1"


def test_grounding_engine():
    # True case
    valid, cites = GroundingEngine.verify_citations(
        "According to the policy [Source: contract_a.pdf, Page 3], coverage is 100%.", 
        ["contract_a.pdf text"]
    )
    assert valid is True
    assert len(cites) == 1
    
    # False case (Hallucination - no citations provided when context is present)
    valid, cites = GroundingEngine.verify_citations(
        "Coverage is definitely 100%. Trust me.", 
        ["contract_a.pdf text"]
    )
    assert valid is False


def test_knowledge_manager_e2e():
    llm = LLMManager()
    km = KnowledgeManager(llm)
    
    async def run():
        doc = await km.add_document("Test Policy", "This policy covers water damage. Fire damage is excluded.")
        assert len(km.documents) == 1
        
        # Test Retrieval
        res = await km.retrieve("water damage", top_k=1)
        assert len(res.results) > 0
        assert "water damage" in res.results[0].chunk.content
        
        # Test summarize
        summary = await km.summarize_document(doc.id)
        # Mock LLM returns "This is a mocked response."
        assert "mocked" in summary

    asyncio.run(run())
