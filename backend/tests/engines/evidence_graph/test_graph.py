import uuid
from app.engines.base import EngineContext, EngineStatus
from app.engines.evidence_graph.manager import EvidenceGraphEngine
from app.engines.extraction.models import ExtractionResult, EntityGroup, ExtractedEntity, Provenance
from app.engines.classification.models import DocumentClass
from app.engines.evidence_graph.models import NodeType, EdgeType


def test_evidence_graph_engine():
    engine = EvidenceGraphEngine()
    
    # Mock Provenance
    mock_prov = Provenance(
        page_index=0,
        bounding_box={"x_min": 0, "y_min": 0, "x_max": 1, "y_max": 1},
        extractor_name="mock_extractor",
        extraction_method="mock"
    )
    
    # 1. Create Mock Extraction Result
    # Group 1: Vehicle 1
    v1_plate = ExtractedEntity(
        id=str(uuid.uuid4()),
        field_name="vehicle_plate",
        raw_value="AB-123-CD",
        normalized_value="AB123CD",
        entity_type="vehicle",
        confidence=0.9,
        provenance=mock_prov
    )
    group1 = EntityGroup(id="G1", group_type="vehicle", entities=[v1_plate])
    
    # Group 2: Vehicle 2 (Same Plate)
    v2_plate = ExtractedEntity(
        id=str(uuid.uuid4()),
        field_name="vehicle_plate",
        raw_value="AB 123 CD",
        normalized_value="AB123CD",
        entity_type="vehicle",
        confidence=0.8,
        provenance=mock_prov
    )
    group2 = EntityGroup(id="G2", group_type="vehicle", entities=[v2_plate])
    
    # Group 3: Policy
    policy_num = ExtractedEntity(
        id=str(uuid.uuid4()),
        field_name="policy_number",
        raw_value="AXA123",
        normalized_value="AXA123",
        entity_type="insurance",
        confidence=0.95,
        provenance=mock_prov
    )
    group3 = EntityGroup(id="G3", group_type="insurance", entities=[policy_num])
    
    extraction_result = ExtractionResult(
        document_class=DocumentClass(family="Constat Amiable"),
        groups=[group1, group2, group3],
        loose_entities=[],
        global_confidence=0.9,
        execution_time_ms=100
    )
    
    # 2. Process
    context = EngineContext(
        claim_id=str(uuid.uuid4()),
        input_data={"extraction_result": extraction_result}
    )
    
    result = engine.process(context)
    
    # 3. Assertions
    if result.status != EngineStatus.SUCCESS:
        print(f"Engine failed with errors: {result.errors}")
    assert result.status == EngineStatus.SUCCESS
    
    graph_data = result.output_data["evidence_graph_result"]
    nodes = graph_data["nodes"]
    edges = graph_data["edges"]
    
    # Nodes: 1 Claim + 3 Groups + 1 Master Vehicle (due to merge)
    assert len(nodes) == 5
    
    # Edges: 3 groups linked to Claim via MENTIONS, 
    # Master Vehicle linked to the 2 duplicate vehicles via IS_SAME_AS,
    # Policy linked to Claim via FILED (Reasoning), 
    # Vehicles linked to Claim via INVOLVED_IN (Reasoning).
    # Master vehicle isn't directly processed by reasoning unless explicitly handled, but base vehicles are.
    
    # Let's check for IS_SAME_AS edges to confirm merger worked
    is_same_as_edges = [e for e in edges if e["edge_type"] == EdgeType.IS_SAME_AS]
    assert len(is_same_as_edges) == 2
    
    # Check that serialization worked
    assert "evidence_graph_json" in result.output_data
    assert "evidence_graph_mermaid" in result.output_data
    
    # Ensure no integrity warnings (this simple graph should be valid)
    assert len(result.output_data["integrity_warnings"]) == 0
