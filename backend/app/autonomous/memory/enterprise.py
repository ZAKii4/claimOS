from typing import Dict, Any, List


class EnterpriseMemoryEngine:
    """Consolidates cross-team knowledge into long-term enterprise memory."""

    _global_memory: List[Dict[str, Any]] = []

    @classmethod
    def get_memory(cls) -> List[Dict[str, Any]]:
        return cls._global_memory

    @classmethod
    def store_knowledge(cls, entry: Dict[str, Any]) -> bool:
        """Stores a new winning strategy or precedent."""
        # Simple deduplication
        if entry not in cls._global_memory:
            cls._global_memory.append(entry)
            return True
        return False

    @classmethod
    def _reset(cls):
        cls._global_memory.clear()
