import time
from typing import List
from app.knowledge.models import SearchQuery, SearchResponse, SearchResult
from app.knowledge.vector_store import MockVectorStore
from app.knowledge.keyword_index import BM25Index
from app.knowledge.reranker import Reranker
from app.knowledge.embeddings import EmbeddingsEngine


class HybridSearchEngine:
    """Orchestrates hybrid retrieval pipeline."""
    
    def __init__(self, vector_store: MockVectorStore, bm25_index: BM25Index, embeddings_engine: EmbeddingsEngine):
        self.vector_store = vector_store
        self.bm25_index = bm25_index
        self.embeddings_engine = embeddings_engine
        
    async def search(self, query: SearchQuery) -> SearchResponse:
        start_time = time.time()
        
        vector_results: List[SearchResult] = []
        bm25_results: List[SearchResult] = []
        
        if query.enable_vector:
            query_vector = await self.embeddings_engine.embed_query(query.query)
            vector_results = self.vector_store.search(query_vector, top_k=query.top_k)
            
        if query.enable_bm25:
            bm25_results = self.bm25_index.search(query.query, top_k=query.top_k)
            
        # Rerank and fuse
        final_results = Reranker.rrf(vector_results, bm25_results)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return SearchResponse(
            query=query.query,
            results=final_results[:query.top_k],
            processing_time_ms=processing_time
        )
