import json
import networkx as nx
from app.engines.evidence_graph.graph import EvidenceGraph


class GraphSerializer:
    """
    Exports the EvidenceGraph to various standard formats.
    """
    
    def to_json(self, graph: EvidenceGraph) -> str:
        """Returns a Neo4j-compatible JSON structure."""
        nodes = [n.model_dump(mode='json') for n in graph.get_all_nodes()]
        edges = [e.model_dump(mode='json') for e in graph.get_all_edges()]
        
        return json.dumps({"nodes": nodes, "edges": edges})

    def to_graphml(self, graph: EvidenceGraph, filepath: str) -> None:
        """
        Exports to GraphML for visualization in Gephi or Cytoscape.
        Since GraphML doesn't support nested dicts (like Pydantic models),
        we flatten the attributes for the export.
        """
        nx_g = graph.nx_graph
        export_g = nx.DiGraph()
        
        for node_id, data in nx_g.nodes(data=True):
            node_obj = data["data"]
            # Flatten primitive attributes
            attrs = {"node_type": node_obj.node_type}
            export_g.add_node(node_id, **attrs)
            
        for u, v, data in nx_g.edges(data=True):
            edge_obj = data["data"]
            export_g.add_edge(u, v, edge_type=edge_obj.edge_type)
            
        nx.write_graphml(export_g, filepath)

    def to_mermaid(self, graph: EvidenceGraph) -> str:
        """Generates a Mermaid.js flowchart string for UI rendering."""
        lines = ["graph TD"]
        for node in graph.get_all_nodes():
            label = f"{node.node_type}\\n{node.id[:8]}"
            lines.append(f'    {node.id}["{label}"]')
            
        for edge in graph.get_all_edges():
            lines.append(f'    {edge.source_id} -->|{edge.edge_type}| {edge.target_id}')
            
        return "\n".join(lines)
