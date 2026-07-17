from typing import Optional

class SemanticCache:
    """
    Short-circuits LLM generation if an exactly similar query was already answered.
    """
    def __init__(self, threshold: float = 0.95):
        self.threshold = threshold
        self._cache = [] # list of dicts: {"query_emb": [...], "response": "..."}

    async def get_cached_response(self, query_embedding: list[float]) -> Optional[str]:
        if not self._cache:
            return None
            
        import numpy as np
        q_vec = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        
        best_sim = 0.0
        best_response = None
        
        for item in self._cache:
            doc_vec = item["query_emb"]
            doc_norm = np.linalg.norm(doc_vec)
            sim = np.dot(q_vec, doc_vec) / (q_norm * doc_norm)
            if sim > best_sim:
                best_sim = sim
                best_response = item["response"]
                
        if best_sim >= self.threshold:
            return best_response
        return None

    async def set_cache(self, query_embedding: list[float], response: str):
        import numpy as np
        self._cache.append({
            "query_emb": np.array(query_embedding, dtype=np.float32),
            "response": response
        })

semantic_cache = SemanticCache()
