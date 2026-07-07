import networkx as nx
from typing import Optional

from app.engines.evidence_graph.models import EvidenceNode, EvidenceEdge, EdgeType, NodeType


class EvidenceGraph:
    """
    Wrapper around NetworkX DiGraph that strictly enforces EvidenceNode and EvidenceEdge constraints.
    """
    def __init__(self):
        self._graph = nx.DiGraph()
        self._nodes_dict: dict[str, EvidenceNode] = {}
        
    def add_node(self, node: EvidenceNode) -> None:
        if node.id not in self._nodes_dict:
            self._nodes_dict[node.id] = node
            # We store the Pydantic model directly as node attribute
            self._graph.add_node(node.id, data=node)

    def add_edge(self, edge: EvidenceEdge) -> None:
        if edge.source_id in self._nodes_dict and edge.target_id in self._nodes_dict:
            self._graph.add_edge(
                edge.source_id, 
                edge.target_id, 
                type=edge.edge_type, 
                data=edge
            )
            
    def get_node(self, node_id: str) -> Optional[EvidenceNode]:
        return self._nodes_dict.get(node_id)
        
    def get_nodes_by_type(self, node_type: NodeType) -> list[EvidenceNode]:
        return [node for node in self._nodes_dict.values() if node.node_type == node_type]
        
    def get_all_nodes(self) -> list[EvidenceNode]:
        return list(self._nodes_dict.values())
        
    def get_all_edges(self) -> list[EvidenceEdge]:
        edges = []
        for u, v, data in self._graph.edges(data=True):
            edges.append(data["data"])
        return edges

    def get_neighbors(self, node_id: str) -> list[EvidenceNode]:
        if node_id not in self._graph:
            return []
        return [self._nodes_dict[n] for n in self._graph.neighbors(node_id)]

    @property
    def nx_graph(self) -> nx.DiGraph:
        """Returns the underlying networkx graph for complex algorithms."""
        return self._graph
