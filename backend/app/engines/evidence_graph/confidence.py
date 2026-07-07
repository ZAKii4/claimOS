from app.engines.evidence_graph.graph import EvidenceGraph
from app.engines.evidence_graph.models import GraphStatistics

class GraphConfidenceScorer:
    """
    Computes global confidence and statistics for the entire Evidence Graph.
    """
    
    def score_graph(self, graph: EvidenceGraph) -> tuple[float, GraphStatistics]:
        nodes = graph.get_all_nodes()
        edges = graph.get_all_edges()
        
        if not nodes:
            return 0.0, GraphStatistics(node_count=0, edge_count=0, connected_components=0, density=0.0)
            
        # Calculate Average Node Confidence
        # N.B. In a real system we would weight this by node type or provenance strength
        avg_confidence = sum(n.confidence.score for n in nodes) / len(nodes)
        
        # Density
        num_nodes = len(nodes)
        possible_edges = num_nodes * (num_nodes - 1)
        density = len(edges) / possible_edges if possible_edges > 0 else 0.0
        
        # In this simple model, more connections = higher confidence
        # We boost the score slightly if density is healthy
        global_confidence = min(1.0, avg_confidence + (density * 0.1))
        
        stats = GraphStatistics(
            node_count=num_nodes,
            edge_count=len(edges),
            connected_components=1, # simplified
            density=density
        )
        
        return round(global_confidence, 3), stats
