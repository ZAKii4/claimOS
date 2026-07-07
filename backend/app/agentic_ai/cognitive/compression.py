from typing import List, Dict, Any


class ContextCompressionEngine:
    """Compresses context dynamically before LLM generation to save memory and tokens."""

    @classmethod
    def compress_context(cls, context_items: List[Dict[str, Any]], max_tokens: int) -> List[Dict[str, Any]]:
        """Simulates intelligent context compression."""
        if not context_items:
            return []
            
        compressed = []
        current_tokens = 0
        
        # In this mock, we assume each item takes ~100 tokens, and we prioritize "EVIDENCE"
        # sort by priority: EVIDENCE > OBSERVATION > SYSTEM
        priority_map = {"EVIDENCE": 1, "OBSERVATION": 2, "SYSTEM": 3}
        
        sorted_items = sorted(
            context_items, 
            key=lambda x: priority_map.get(x.get("type", "SYSTEM"), 99)
        )
        
        for item in sorted_items:
            token_cost = item.get("token_cost", 100)
            if current_tokens + token_cost <= max_tokens:
                compressed.append(item)
                current_tokens += token_cost
            else:
                # Summarization simulation placeholder if over budget
                compressed.append({
                    "type": "SUMMARY",
                    "content": f"Summarized {len(sorted_items) - len(compressed)} remaining items."
                })
                break
                
        return compressed
