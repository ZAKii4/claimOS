from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# ─────────────────────────────────────────────────────
# Digital Twin
# ─────────────────────────────────────────────────────

class DigitalTwin(BaseModel):
    """Immutable snapshot of a complete claim state."""
    id: str
    claim_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_graph: Dict[str, Any] = Field(default_factory=dict)
    validation_report: Dict[str, Any] = Field(default_factory=dict)
    decision_report: Dict[str, Any] = Field(default_factory=dict)
    workflow_state: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class TwinSnapshot(BaseModel):
    twin_id: str
    label: str  # e.g. "before_simulation", "after_simulation"
    state: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────────────────
# Scenario & Simulation
# ─────────────────────────────────────────────────────

class ScenarioMutation(BaseModel):
    """A single change to apply during a simulation."""
    field: str          # e.g. "ocr_confidence", "fraud_score"
    original_value: Any = None
    new_value: Any = None


class Scenario(BaseModel):
    id: str
    name: str
    description: str = ""
    mutations: List[ScenarioMutation] = Field(default_factory=list)


class SimulationResult(BaseModel):
    scenario_id: str
    twin_id: str
    original_decision: str = ""
    simulated_decision: str = ""
    original_risk: str = ""
    simulated_risk: str = ""
    diff: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, float] = Field(default_factory=dict)


class ComparisonReport(BaseModel):
    scenario_a: str
    scenario_b: str
    results_a: SimulationResult
    results_b: SimulationResult
    diff_summary: Dict[str, Any] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────
# Explainable AI
# ─────────────────────────────────────────────────────

class RuleImpact(BaseModel):
    rule_name: str
    result: str          # "PASS" or "FAIL"
    weight: float = 1.0
    impact_on_decision: str = ""  # e.g. "Blocked AUTO_APPROVE"
    evidence_ref: Optional[str] = None


class ConfidenceBreakdown(BaseModel):
    ocr: float = 0.0
    iqa: float = 0.0
    classification: float = 0.0
    extraction: float = 0.0
    validation: float = 0.0
    risk: float = 0.0
    decision: float = 0.0
    consensus: float = 0.0
    global_score: float = 0.0


class DecisionPathNode(BaseModel):
    step: str
    value: str
    confidence: float = 0.0


class ExplanationReport(BaseModel):
    claim_id: str
    decision: str
    decision_path: List[DecisionPathNode] = Field(default_factory=list)
    rules_executed: List[RuleImpact] = Field(default_factory=list)
    confidence_breakdown: ConfidenceBreakdown = Field(default_factory=ConfidenceBreakdown)
    evidence_sources: List[Dict[str, Any]] = Field(default_factory=list)
    mermaid_graph: str = ""


# ─────────────────────────────────────────────────────
# Monte Carlo & Optimization
# ─────────────────────────────────────────────────────

class MonteCarloReport(BaseModel):
    iterations: int
    decision_distribution: Dict[str, int] = Field(default_factory=dict)
    stability: float = 0.0       # % of majority decision
    variance: float = 0.0
    confidence_interval: Dict[str, float] = Field(default_factory=dict)


class SensitivityAnalysis(BaseModel):
    parameter: str
    impact_score: float = 0.0    # How much does varying this change the outcome?
    critical_threshold: Optional[float] = None


class OptimizationReport(BaseModel):
    objective: str               # e.g. "maximize_automation"
    best_thresholds: Dict[str, float] = Field(default_factory=dict)
    predicted_automation_rate: float = 0.0
    predicted_error_rate: float = 0.0
    iterations_run: int = 0
