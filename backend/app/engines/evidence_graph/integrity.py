import networkx as nx
from app.engines.evidence_graph.graph import EvidenceGraph
from app.engines.evidence_graph.models import NodeType

class GraphIntegrityChecker:
    """
    Validates structural invariants of the Evidence Graph.
    """
    
    def check_integrity(self, graph: EvidenceGraph) -> list[str]:
        errors = []
        nx_g = graph.nx_graph
        
        # 1. No isolated structural nodes (Vehicles, Policies must be connected to something)
        for node in graph.get_all_nodes():
            if node.node_type in [NodeType.VEHICLE, NodeType.POLICY]:
                if nx_g.degree(node.id) == 0:
                    errors.append(f"Orphan Node Detected: {node.node_type} ({node.id}) is completely isolated.")
                    
        # 2. Cycles check (Optional depending on design, knowledge graphs can have cycles, 
        # but hierarchical ownership should be a DAG).
        # We skip cycle detection for the generic graph but it can be implemented here.
        
        return errors
