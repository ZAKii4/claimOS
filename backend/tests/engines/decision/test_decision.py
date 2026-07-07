import uuid
from app.engines.base import EngineContext, EngineStatus
from app.engines.decision.manager import DecisionEngine
from app.engines.evidence_graph.models import EvidenceGraphResult
from app.engines.validation.report import ValidationReport, ValidationSummary, ValidationStatistics, ValidationIssue
from app.engines.validation.severity import ValidationSeverity
from app.engines.decision.models import DecisionType, QueueName


def test_decision_engine_auto_approve():
    engine = DecisionEngine()
    
    # 1. Perfect graph & validation
    graph = EvidenceGraphResult(claim_id="123", nodes=[], edges=[], global_confidence=1.0)
    report = ValidationReport(
        claim_id="123",
        summary=ValidationSummary(is_valid=True, global_score=0.99, has_blockers=False, has_criticals=False),
        statistics=ValidationStatistics()
    )
    
    context = EngineContext(claim_id="123", input_data={"evidence_graph_result": graph, "validation_report": report})
    
    result = engine.process(context)
    assert result.status == EngineStatus.SUCCESS
    decision = result.output_data["decision_result"]
    
    assert decision["decision"] == DecisionType.AUTO_APPROVED
    assert decision["routing"] == QueueName.AUTO_PROCESSING
    assert len(decision["audit_entries"]) == 1
    assert decision["audit_entries"][0]["strategy_used"] == "AutoApproveStrategy"


def test_decision_engine_reject_blocker():
    engine = DecisionEngine()
    
    graph = EvidenceGraphResult(claim_id="123", nodes=[], edges=[], global_confidence=1.0)
    issue = ValidationIssue(
        rule_id="COMP-001", rule_name="Empty", category="COMP", 
        severity=ValidationSeverity.BLOCKER, message="No docs", explanation=""
    )
    report = ValidationReport(
        claim_id="123",
        summary=ValidationSummary(is_valid=False, global_score=0.0, has_blockers=True, has_criticals=False),
        statistics=ValidationStatistics(),
        issues=[issue]
    )
    
    context = EngineContext(claim_id="123", input_data={"evidence_graph_result": graph, "validation_report": report})
    
    result = engine.process(context)
    assert result.status == EngineStatus.SUCCESS
    decision = result.output_data["decision_result"]
    
    assert decision["decision"] == DecisionType.AUTO_REJECTED
    assert decision["audit_entries"][0]["strategy_used"] == "RejectStrategy"


def test_decision_engine_fraud():
    engine = DecisionEngine()
    
    graph = EvidenceGraphResult(claim_id="123", nodes=[], edges=[], global_confidence=1.0)
    report = ValidationReport(
        claim_id="123",
        summary=ValidationSummary(is_valid=True, global_score=0.8, has_blockers=False, has_criticals=False),
        statistics=ValidationStatistics(issues_by_category={"FRAUD_HEURISTIC": 5}), # Fraud triggers at > 0
    )
    
    context = EngineContext(claim_id="123", input_data={"evidence_graph_result": graph, "validation_report": report})
    
    result = engine.process(context)
    assert result.status == EngineStatus.SUCCESS
    decision = result.output_data["decision_result"]
    
    assert decision["decision"] == DecisionType.FRAUD_REVIEW
    assert decision["routing"] == QueueName.FRAUD
    assert decision["audit_entries"][0]["strategy_used"] == "FraudReviewStrategy"
