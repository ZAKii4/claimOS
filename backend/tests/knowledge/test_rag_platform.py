import pytest
import asyncio
from app.knowledge.manager import KnowledgeManager
from app.knowledge.chunking import ChunkingEngine
from app.knowledge.keyword_index import BM25Index
from app.knowledge.reranker import Reranker
from app.knowledge.citation import GroundingEngine
from app.llm.manager import LLMManager
from app.knowledge.models import KnowledgeChunk, SearchResult

requires_ollama = pytest.mark.requires_ollama


class MockVectorStore:
    def __init__(self):
        self.chunks = []
        
    def add_chunks(self, chunks):
        self.chunks.extend(chunks)
        
    def search(self, query_vector, top_k=5):
        results = []
        for c in self.chunks:
            if not c.vector:
                continue
            # compute simple dot product
            score = sum(q * v for q, v in zip(query_vector, c.vector))
            results.append(SearchResult(chunk=c, score=score, vector_score=score))
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]



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


@requires_ollama
def test_knowledge_manager_e2e():
    llm = LLMManager()
    mock_store = MockVectorStore()
    km = KnowledgeManager(llm, vector_store=mock_store, session_factory=None)

    async def run():
        doc = await km.add_document("Test Policy", "This policy covers water damage. Fire damage is excluded.", persist_to_db=False)
        assert any(d.id == doc.id for d in km.documents)

        # Test Retrieval
        res = await km.retrieve("water damage", top_k=1)
        # BM25 and/or vector search should find the right chunk
        assert len(res.results) > 0

        # Test summarize (uses in-memory chunks, not DB) — must be a real,
        # non-empty LLM-generated summary, not the removed Mock fallback.
        summary = await km.summarize_document(doc.id)
        assert summary.strip() != ""
        assert "mocked response" not in summary.lower()

    asyncio.run(run())

