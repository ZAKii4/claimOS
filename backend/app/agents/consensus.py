from typing import List, Dict, Any


class ConsensusEngine:
    """
    Resolves conflicts when multiple agents provide overlapping or conflicting results.
    """
    
    @staticmethod
    def majority_voting(opinions: List[str]) -> str:
        if not opinions:
            return "UNKNOWN"
        counts = {}
        for op in opinions:
            counts[op] = counts.get(op, 0) + 1
            
        # Return key with max count
        return max(counts, key=counts.get)
        
    @staticmethod
    def confidence_aggregation(opinions_with_confidence: List[Dict[str, Any]]) -> str:
        """
        Input format: [{"value": "FRAUD", "confidence": 0.9}, {"value": "CLEAN", "confidence": 0.4}]
        """
        if not opinions_with_confidence:
            return "UNKNOWN"
            
        scores = {}
        for op in opinions_with_confidence:
            val = op["value"]
            conf = op["confidence"]
            scores[val] = scores.get(val, 0.0) + conf
            
        return max(scores, key=scores.get)
