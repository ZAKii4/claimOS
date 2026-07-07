import networkx as nx
from app.engines.evidence_graph.graph import EvidenceGraph
from app.engines.evidence_graph.models import NodeType, EdgeType, EvidenceEdge


class GraphReasoningEngine:
    """
    Deterministic rule-based reasoning on the graph structure.
    E.g. If Vehicle is mentioned in Claim, and Person is mentioned in Claim, link Person -> DRIVES -> Vehicle
    (Highly simplified heuristic for the MVP).
    """

    def apply_rules(self, graph: EvidenceGraph) -> None:
        nx_g = graph.nx_graph
        
        # Rule 1: Link Policy to Claim
        claims = graph.get_nodes_by_type(NodeType.CLAIM)
        policies = graph.get_nodes_by_type(NodeType.POLICY)
        
        for claim in claims:
            for policy in policies:
                if not nx_g.has_edge(policy.id, claim.id):
                    graph.add_edge(EvidenceEdge(
                        source_id=policy.id,
                        target_id=claim.id,
                        edge_type=EdgeType.FILED
                    ))
                    
        # Rule 2: Link Vehicle to Claim
        vehicles = graph.get_nodes_by_type(NodeType.VEHICLE)
        for claim in claims:
            for vehicle in vehicles:
                if not nx_g.has_edge(vehicle.id, claim.id) and not nx_g.has_edge(claim.id, vehicle.id):
                    graph.add_edge(EvidenceEdge(
                        source_id=vehicle.id,
                        target_id=claim.id,
                        edge_type=EdgeType.INVOLVED_IN
                    ))
