from app.engines.evidence_graph.graph import EvidenceGraph
from app.engines.evidence_graph.models import NodeType


class EntityResolver:
    """
    Identifies nodes that represent the same real-world entity 
    (e.g., two VEHICLE nodes with the same license plate).
    """
    def resolve_duplicates(self, graph: EvidenceGraph) -> list[tuple[str, str]]:
        """
        Returns a list of tuples (node_id_1, node_id_2) that should be merged.
        """
        duplicates = []
        vehicles = graph.get_nodes_by_type(NodeType.VEHICLE)
        
        # Naive O(N^2) comparison for identical license plates
        for i in range(len(vehicles)):
            for j in range(i + 1, len(vehicles)):
                v1 = vehicles[i]
                v2 = vehicles[j]
                
                plate1 = self._extract_plate(v1)
                plate2 = self._extract_plate(v2)
                
                if plate1 and plate2 and plate1 == plate2:
                    duplicates.append((v1.id, v2.id))
                    
        return duplicates
        
    def _extract_plate(self, node) -> str | None:
        entities = node.attributes.get("entities", [])
        for e in entities:
            if e.get("field_name") == "vehicle_plate":
                return e.get("normalized_value")
        return None
