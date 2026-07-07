import math
from collections import Counter
from typing import List, Dict
from app.knowledge.models import KnowledgeChunk, SearchResult


class BM25Index:
    """Pure Python implementation of Okapi BM25 for keyword search."""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.chunks: List[KnowledgeChunk] = []
        self.doc_freqs: Dict[str, int] = Counter()
        self.doc_lengths: List[int] = []
        self.avgdl: float = 0.0
        self.N: int = 0
        self.term_freqs: List[Counter] = []
        
    def _tokenize(self, text: str) -> List[str]:
        # Very naive tokenization for MVP
        import re
        return re.findall(r'\w+', text.lower())
        
    def add_chunks(self, chunks: List[KnowledgeChunk]):
        for chunk in chunks:
            self.chunks.append(chunk)
            tokens = self._tokenize(chunk.content)
            self.doc_lengths.append(len(tokens))
            freq = Counter(tokens)
            self.term_freqs.append(freq)
            
            for term in freq.keys():
                self.doc_freqs[term] += 1
                
        self.N = len(self.chunks)
        self.avgdl = sum(self.doc_lengths) / self.N if self.N > 0 else 0
        
    def _idf(self, q: str) -> float:
        df = self.doc_freqs.get(q, 0)
        return math.log(1 + (self.N - df + 0.5) / (df + 0.5))
        
    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        q_tokens = self._tokenize(query)
        if not q_tokens or self.N == 0:
            return []
            
        scores = []
        for idx, chunk in enumerate(self.chunks):
            score = 0.0
            dl = self.doc_lengths[idx]
            freqs = self.term_freqs[idx]
            
            for q in q_tokens:
                if q in freqs:
                    tf = freqs[q]
                    idf = self._idf(q)
                    numerator = tf * (self.k1 + 1)
                    denominator = tf + self.k1 * (1 - self.b + self.b * (dl / self.avgdl))
                    score += idf * (numerator / denominator)
                    
            if score > 0:
                scores.append(SearchResult(chunk=chunk, score=score, bm25_score=score))
                
        scores.sort(key=lambda x: x.bm25_score, reverse=True)
        return scores[:top_k]
