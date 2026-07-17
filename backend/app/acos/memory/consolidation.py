from typing import List, Dict, Any


class MemoryConsolidationEngine:
    """Merges, deduplicates, and archives cognitive memory streams."""

    @classmethod
    def consolidate(cls, short_term_items: List[Dict[str, Any]], episodic_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simulates memory consolidation algorithm."""
        
        merged_memory = []
        archived_count = 0
        
        all_items = short_term_items + episodic_items
        seen_contents = set()
        
        for item in all_items:
            content = item.get("content", "")
            # Deduplication
            if content not in seen_contents:
                # Check for obsolete info (mocking rule: if "obsolete" in content)
                if "obsolete" in content.lower():
                    archived_count += 1
                else:
                    merged_memory.append(item)
                    seen_contents.add(content)
            else:
                # Duplicate found
                archived_count += 1
                
        return {
            "status": "CONSOLIDATED",
            "active_items": len(merged_memory),
            "archived_items": archived_count,
            "memory": merged_memory
        }
