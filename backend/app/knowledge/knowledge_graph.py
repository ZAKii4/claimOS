from typing import Dict, List, Set


class DocumentGraph:
    """
    Semantic graph linking documents, procedures, and concepts.
    Independent from the Evidence Graph (Phase 9).
    """
    def __init__(self):
        self.nodes: Set[str] = set()
        self.edges: Dict[str, List[str]] = {}
        
    def add_relation(self, source_id: str, target_id: str, relation_type: str):
        self.nodes.add(source_id)
        self.nodes.add(target_id)
        
        if source_id not in self.edges:
            self.edges[source_id] = []
        self.edges[source_id].append(target_id)
        
    def get_related_documents(self, doc_id: str) -> List[str]:
        return self.edges.get(doc_id, [])
