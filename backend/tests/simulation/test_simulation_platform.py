import pytest
from app.simulation.digital_twin import DigitalTwinEngine
from app.simulation.simulator import SimulationEngine
from app.simulation.explainer import ExplainerEngine
from app.simulation.monte_carlo import MonteCarloEngine
from app.simulation.optimizer import OptimizationEngine
from app.simulation.models import Scenario, ScenarioMutation


# ─────────────────────────────────────────────────────
# Helper: build a realistic twin
# ─────────────────────────────────────────────────────

def _make_twin(**overrides):
    defaults = dict(
        claim_id="CLM-001",
        documents=[{"id": "doc1", "type": "medical_certificate", "page": 1, "provenance": "pipeline"}],
        evidence_graph={"entities": 23, "relations": 15},
        validation_report={"score": 0.96, "warnings": 1, "rules": [
            {"name": "AmountCheck", "result": "PASS", "weight": 1.0, "impact": "None"},
            {"name": "DateCheck", "result": "PASS", "weight": 1.0, "impact": "None"},
        ]},
        decision_report={"decision": "AUTO_APPROVED", "risk_level": "LOW"},
        metrics={
            "ocr_confidence": 0.95, "iqa_score": 0.88,
            "classification_confidence": 0.97, "extraction_confidence": 0.91,
            "entity_count": 23, "fraud_score": 0.05,
            "risk_score": 0.1, "decision_confidence": 0.96, "consensus_score": 0.92,
        },
    )
    defaults.update(overrides)
    return DigitalTwinEngine.create_twin(**defaults)


# ─────────────────────────────────────────────────────
# Digital Twin — Creation & Isolation
# ─────────────────────────────────────────────────────

def test_create_digital_twin():
    twin = _make_twin()
    assert twin.claim_id == "CLM-001"
    assert twin.decision_report["decision"] == "AUTO_APPROVED"
    assert len(twin.documents) == 1


def test_twin_isolation():
    """Mutations on a clone must NOT affect the original."""
    original = _make_twin()
    clone = DigitalTwinEngine.clone_for_simulation(original)

    # Mutate clone
    clone.decision_report["decision"] = "FRAUD_REVIEW"
    clone.documents.append({"id": "doc2"})

    # Original is untouched
    assert original.decision_report["decision"] == "AUTO_APPROVED"
    assert len(original.documents) == 1


def test_snapshot():
    twin = _make_twin()
    snap = DigitalTwinEngine.snapshot(twin, "before")
    assert snap.label == "before"
    assert snap.state["decision_report"]["decision"] == "AUTO_APPROVED"


# ─────────────────────────────────────────────────────
# Simulation — What-If
# ─────────────────────────────────────────────────────

def test_whatif_lower_validation_score():
    """Lowering validation score should change decision from AUTO_APPROVED to HUMAN_REVIEW."""
    twin = _make_twin()
    scenario = Scenario(
        id="s1", name="Lower validation",
        mutations=[ScenarioMutation(field="validation_report.score", new_value=0.80)],
    )
    result = SimulationEngine.simulate(twin, scenario)

    assert result.original_decision == "AUTO_APPROVED"
    assert result.simulated_decision == "HUMAN_REVIEW"
    assert "decision" in result.diff


def test_whatif_high_fraud_score():
    """High fraud score should trigger FRAUD_REVIEW regardless of validation."""
    twin = _make_twin()
    scenario = Scenario(
        id="s2", name="Fraud spike",
        mutations=[ScenarioMutation(field="metrics.fraud_score", new_value=0.95)],
    )
    result = SimulationEngine.simulate(twin, scenario)

    assert result.simulated_decision == "FRAUD_REVIEW"
    assert result.simulated_risk == "CRITICAL"

    # Original twin is untouched
    assert twin.decision_report["decision"] == "AUTO_APPROVED"


def test_scenario_comparison():
    twin = _make_twin()
    sc_a = Scenario(id="a", name="Lenient", mutations=[
        ScenarioMutation(field="validation_report.score", new_value=0.98),
    ])
    sc_b = Scenario(id="b", name="Strict", mutations=[
        ScenarioMutation(field="validation_report.score", new_value=0.60),
    ])
    report = SimulationEngine.compare(twin, sc_a, sc_b)

    assert report.results_a.simulated_decision == "AUTO_APPROVED"
    assert report.results_b.simulated_decision == "AUTO_REJECTED"
    assert report.diff_summary["same_outcome"] is False


# ─────────────────────────────────────────────────────
# Explainable AI
# ─────────────────────────────────────────────────────

def test_explain_decision():
    twin = _make_twin()
    report = ExplainerEngine.explain_decision(twin)

    assert report.claim_id == "CLM-001"
    assert report.decision == "AUTO_APPROVED"
    assert len(report.decision_path) == 7  # IQA, OCR, Classification, Extraction, Validation, Risk, Decision
    assert report.decision_path[0].step == "Image Quality"
    assert report.decision_path[-1].step == "Decision"


def test_confidence_breakdown():
    twin = _make_twin()
    report = ExplainerEngine.explain_decision(twin)
    bd = report.confidence_breakdown

    assert bd.ocr == 0.95
    assert bd.iqa == 0.88
    assert bd.global_score > 0  # Average of non-zero scores


def test_decision_graph_mermaid():
    twin = _make_twin()
    report = ExplainerEngine.explain_decision(twin)

    assert "graph TD" in report.mermaid_graph
    assert "step_0" in report.mermaid_graph
    assert "step_6" in report.mermaid_graph
    assert "-->" in report.mermaid_graph


def test_rule_impacts():
    twin = _make_twin()
    report = ExplainerEngine.explain_decision(twin)

    assert len(report.rules_executed) == 2
    assert report.rules_executed[0].rule_name == "AmountCheck"
    assert report.rules_executed[0].result == "PASS"


def test_evidence_sources():
    twin = _make_twin()
    report = ExplainerEngine.explain_decision(twin)

    assert len(report.evidence_sources) == 1
    assert report.evidence_sources[0]["document_id"] == "doc1"


# ─────────────────────────────────────────────────────
# Monte Carlo
# ─────────────────────────────────────────────────────

def test_monte_carlo():
    twin = _make_twin()
    report = MonteCarloEngine.run(twin, iterations=50, seed=42)

    assert report.iterations == 50
    assert sum(report.decision_distribution.values()) == 50
    assert 0.0 <= report.stability <= 1.0
    assert len(report.confidence_interval) > 0


def test_monte_carlo_reproducibility():
    """Same seed should produce identical results."""
    twin = _make_twin()
    r1 = MonteCarloEngine.run(twin, iterations=50, seed=123)
    r2 = MonteCarloEngine.run(twin, iterations=50, seed=123)

    assert r1.decision_distribution == r2.decision_distribution
    assert r1.stability == r2.stability


# ─────────────────────────────────────────────────────
# Optimization
# ─────────────────────────────────────────────────────

def test_optimizer():
    twins = [
        _make_twin(claim_id="A", validation_report={"score": 0.98}, metrics={"fraud_score": 0.01}),
        _make_twin(claim_id="B", validation_report={"score": 0.75}, metrics={"fraud_score": 0.02}),
        _make_twin(claim_id="C", validation_report={"score": 0.50}, metrics={"fraud_score": 0.90}),
    ]
    report = OptimizationEngine.optimize(twins, step=0.1)

    assert report.objective == "maximize_automation"
    assert report.iterations_run > 0
    assert "validation_threshold" in report.best_thresholds
