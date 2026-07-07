import uuid
from app.engines.base import EngineContext, EngineStatus
from app.engines.validation.manager import ValidationEngine
from app.engines.evidence_graph.models import EvidenceGraphResult, EvidenceNode, NodeType
from app.engines.validation.severity import ValidationSeverity


def test_validation_engine_empty_graph():
    engine = ValidationEngine()
    
    # 1. Create Empty Graph
    graph_result = EvidenceGraphResult(
        claim_id=str(uuid.uuid4()),
        nodes=[],
        edges=[],
        global_confidence=0.0
    )
    
    context = EngineContext(
        claim_id=graph_result.claim_id,
        input_data={"evidence_graph_result": graph_result}
    )
    
    # 2. Process
    result = engine.process(context)
    
    # 3. Assertions
    assert result.status == EngineStatus.SUCCESS
    report = result.output_data["validation_report"]
    
    assert report["summary"]["is_valid"] is False
    assert report["summary"]["has_blockers"] is True
    
    issues = report["issues"]
    assert any(i["rule_id"] == "COMP-001" for i in issues)


def test_validation_engine_orphan_nodes():
    engine = ValidationEngine()
    
    # 1. Create Graph with an Orphan Vehicle
    orphan_vehicle = EvidenceNode(
        id=str(uuid.uuid4()),
        node_type=NodeType.VEHICLE
    )
    
    graph_result = EvidenceGraphResult(
        claim_id=str(uuid.uuid4()),
        nodes=[orphan_vehicle],
        edges=[],
        global_confidence=1.0
    )
    
    context = EngineContext(
        claim_id=graph_result.claim_id,
        input_data={"evidence_graph_result": graph_result}
    )
    
    # 2. Process
    result = engine.process(context)
    
    # 3. Assertions
    assert result.status == EngineStatus.SUCCESS
    report = result.output_data["validation_report"]
    
    issues = report["issues"]
    orphan_issue = next((i for i in issues if i["rule_id"] == "GRPH-001"), None)
    assert orphan_issue is not None
    assert orphan_issue["severity"] == ValidationSeverity.WARNING
    assert orphan_issue["target_node_id"] == orphan_vehicle.id


def test_validation_engine_plate_mismatch():
    engine = ValidationEngine()
    
    # 1. Create Graph with duplicated plates (unmerged)
    v1 = EvidenceNode(
        id="v1",
        node_type=NodeType.VEHICLE,
        attributes={"entities": [{"field_name": "vehicle_plate", "normalized_value": "XX111YY"}]}
    )
    v2 = EvidenceNode(
        id="v2",
        node_type=NodeType.VEHICLE,
        attributes={"entities": [{"field_name": "vehicle_plate", "normalized_value": "XX111YY"}]}
    )
    
    graph_result = EvidenceGraphResult(
        claim_id=str(uuid.uuid4()),
        nodes=[v1, v2],
        edges=[],
        global_confidence=1.0
    )
    
    context = EngineContext(
        claim_id=graph_result.claim_id,
        input_data={"evidence_graph_result": graph_result}
    )
    
    # 2. Process
    result = engine.process(context)
    
    # 3. Assertions
    report = result.output_data["validation_report"]
    
    issues = report["issues"]
    mismatch_issue = next((i for i in issues if i["rule_id"] == "CONS-001"), None)
    assert mismatch_issue is not None
    assert mismatch_issue["severity"] == ValidationSeverity.CRITICAL
    assert report["summary"]["has_criticals"] is True
