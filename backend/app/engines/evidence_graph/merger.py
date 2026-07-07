import uuid
from app.engines.evidence_graph.graph import EvidenceGraph
from app.engines.evidence_graph.models import EvidenceNode, EvidenceEdge, EdgeType


class GraphMerger:
    """
    Executes additive merging: Creates a Master Node linked to the duplicates via IS_SAME_AS.
    """
    def merge(self, graph: EvidenceGraph, duplicates: list[tuple[str, str]]) -> None:
        for node1_id, node2_id in duplicates:
            n1 = graph.get_node(node1_id)
            n2 = graph.get_node(node2_id)
            
            if not n1 or not n2:
                continue
                
            # Create Master Node
            master_id = f"MASTER-{uuid.uuid4()}"
            
            # Merge attributes and provenances
            master_attrs = {**n1.attributes, **n2.attributes}
            master_provenances = n1.provenances + n2.provenances
            
            master_node = EvidenceNode(
                id=master_id,
                node_type=n1.node_type,  # Assuming they have the same type since they matched
                attributes=master_attrs,
                provenances=master_provenances
            )
            
            graph.add_node(master_node)
            
            # Link duplicates to Master Node
            graph.add_edge(EvidenceEdge(
                source_id=master_id,
                target_id=n1.id,
                edge_type=EdgeType.IS_SAME_AS
            ))
            graph.add_edge(EvidenceEdge(
                source_id=master_id,
                target_id=n2.id,
                edge_type=EdgeType.IS_SAME_AS
            ))
