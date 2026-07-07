import math
from typing import List, Dict
from app.knowledge.models import KnowledgeChunk, SearchResult


class BaseVectorStore:
    def add_chunks(self, chunks: List[KnowledgeChunk]):
        pass
        
    def search(self, query_vector: List[float], top_k: int = 5) -> List[SearchResult]:
        pass


class MockVectorStore(BaseVectorStore):
    """Pure Python in-memory vector store using Cosine Similarity."""
    
    def __init__(self):
        self.chunks: List[KnowledgeChunk] = []
        
    def add_chunks(self, chunks: List[KnowledgeChunk]):
        self.chunks.extend(chunks)
        
    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
            
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm_v1 = math.sqrt(sum(a * a for a in v1))
        norm_v2 = math.sqrt(sum(b * b for b in v2))
        
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
            
        return dot_product / (norm_v1 * norm_v2)
        
    def search(self, query_vector: List[float], top_k: int = 5) -> List[SearchResult]:
        if not query_vector:
            return []
            
        results = []
        for chunk in self.chunks:
            if chunk.vector:
                score = self._cosine_similarity(query_vector, chunk.vector)
                results.append(SearchResult(chunk=chunk, score=score, vector_score=score))
                
        results.sort(key=lambda x: x.vector_score, reverse=True)
        return results[:top_k]
