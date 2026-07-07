from typing import List, Dict
from app.knowledge.models import SearchResult


class Reranker:
    """Implements Reciprocal Rank Fusion (RRF) for hybrid search."""
    
    @staticmethod
    def rrf(vector_results: List[SearchResult], keyword_results: List[SearchResult], k: int = 60) -> List[SearchResult]:
        """
        Combines two ranked lists using RRF.
        score = 1 / (k + rank)
        """
        scores: Dict[str, SearchResult] = {}
        
        def _add_rank_score(results: List[SearchResult], is_vector: bool):
            for rank, res in enumerate(results):
                chunk_id = res.chunk.id
                if chunk_id not in scores:
                    # Create a new merged result object
                    scores[chunk_id] = SearchResult(
                        chunk=res.chunk,
                        score=0.0,
                        vector_score=res.vector_score if is_vector else 0.0,
                        bm25_score=res.bm25_score if not is_vector else 0.0
                    )
                else:
                    if is_vector:
                        scores[chunk_id].vector_score = res.vector_score
                    else:
                        scores[chunk_id].bm25_score = res.bm25_score
                        
                # Add RRF score
                rrf_score = 1.0 / (k + rank + 1)
                scores[chunk_id].score += rrf_score
                
        _add_rank_score(vector_results, is_vector=True)
        _add_rank_score(keyword_results, is_vector=False)
        
        merged = list(scores.values())
        merged.sort(key=lambda x: x.score, reverse=True)
        return merged
