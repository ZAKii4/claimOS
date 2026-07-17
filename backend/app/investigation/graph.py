from typing import Dict, Any

class InteractiveEvidenceGraph:
    """Prepares evidence graphs for interactive frontend exploration."""

    @classmethod
    def get_graph(cls, claim_id: str) -> Dict[str, Any]:
        return {
            "claim_id": claim_id,
            "nodes": [
                {"id": "doc_1", "label": "Invoice A", "group": "Document"},
                {"id": "person_1", "label": "John Doe", "group": "PolicyHolder"}
            ],
            "edges": [
                {"from": "person_1", "to": "doc_1", "label": "SUBMITTED"}
            ]
        }
