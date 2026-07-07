import uuid

from app.engines.evidence_graph.graph import EvidenceGraph
from app.engines.evidence_graph.models import EvidenceNode, EvidenceEdge, NodeType, EdgeType
from app.engines.extraction.models import ExtractionResult, EntityGroup


class GraphBuilder:
    """
    Ingests an ExtractionResult and builds the initial unmerged EvidenceGraph.
    """

    def build(self, extraction_result: ExtractionResult, claim_id: str) -> EvidenceGraph:
        graph = EvidenceGraph()
        
        # 1. Create a root Claim Node
        claim_node = EvidenceNode(
            id=str(claim_id),
            node_type=NodeType.CLAIM,
            attributes={"classification": extraction_result.document_class.model_dump()}
        )
        graph.add_node(claim_node)
        
        # 2. Iterate through groups
        for group in extraction_result.groups:
            # We map the group to a logical node (e.g. VEHICLE or PERSON depending on group type)
            # For MVP, we determine node type heuristically from entity types inside the group
            node_type = self._determine_node_type(group)
            
            group_node = EvidenceNode(
                id=group.id,
                node_type=node_type,
                attributes={"entities": [e.model_dump() for e in group.entities]},
                provenances=[e.provenance for e in group.entities]
            )
            graph.add_node(group_node)
            
            # Link to claim (Basic heuristic: Claim Mentions Vehicle)
            graph.add_edge(EvidenceEdge(
                source_id=claim_node.id,
                target_id=group_node.id,
                edge_type=EdgeType.MENTIONS
            ))
            
        # 3. Process loose entities (could be individual attributes or independent nodes)
        for entity in extraction_result.loose_entities:
            loose_node = EvidenceNode(
                id=entity.id,
                node_type=self._map_entity_type_to_node_type(entity.entity_type),
                attributes={"field": entity.field_name, "value": entity.normalized_value},
                provenances=[entity.provenance]
            )
            graph.add_node(loose_node)
            graph.add_edge(EvidenceEdge(
                source_id=claim_node.id,
                target_id=loose_node.id,
                edge_type=EdgeType.HAS_ATTRIBUTE
            ))
            
        return graph

    def _determine_node_type(self, group: EntityGroup) -> NodeType:
        types = [e.entity_type for e in group.entities]
        if "vehicle" in types:
            return NodeType.VEHICLE
        if "person" in types:
            return NodeType.PERSON
        if "insurance" in types:
            return NodeType.POLICY
        return NodeType.UNKNOWN

    def _map_entity_type_to_node_type(self, entity_type: str) -> NodeType:
        mapping = {
            "vehicle": NodeType.VEHICLE,
            "person": NodeType.PERSON,
            "insurance": NodeType.POLICY,
            "medical": NodeType.MEDICAL_CERTIFICATE,
            "police": NodeType.POLICE_REPORT
        }
        return mapping.get(entity_type, NodeType.UNKNOWN)
