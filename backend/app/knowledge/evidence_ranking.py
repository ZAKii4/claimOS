from typing import List, Dict, Any

class EvidenceRanking:
    """
    Scores and ranks evidence retrieved from Hybrid Search based on:
    - Freshness
    - Source Reliability
    - Similarity
    """
    async def rank_evidence(self, evidences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for ev in evidences:
            score = ev.get("score", 0.5)
            # Boost score based on metadata
            metadata = ev.get("metadata", {})
            if metadata.get("is_verified"):
                score += 0.2
            if metadata.get("source") == "official":
                score += 0.1
            ev["final_score"] = min(score, 1.0)
            
        evidences.sort(key=lambda x: x["final_score"], reverse=True)
        return evidences

evidence_ranking = EvidenceRanking()
