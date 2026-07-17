from typing import Dict, Any, List

class EnterpriseSearchEngine:
    """Global multi-modal semantic search index."""

    @classmethod
    def search(cls, query: str) -> List[Dict[str, Any]]:
        return [
            {"type": "CLAIM", "id": "CLM-99", "score": 0.98},
            {"type": "DOCUMENT", "id": "DOC-45", "score": 0.85},
            {"type": "WORKFLOW", "id": "WF-12", "score": 0.76}
        ]
