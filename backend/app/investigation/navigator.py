from typing import Dict, Any, List

class KnowledgeNavigator:
    """Visual exploration of the global knowledge graph."""

    @classmethod
    def explore_node(cls, node_id: str) -> Dict[str, Any]:
        return {
            "node": node_id,
            "neighbors": ["LegalGuide.pdf", "Previous_Claim_109"],
            "type": "DOCUMENT"
        }
