import copy
from typing import Dict, Any, List
from app.simulation.models import (
    Scenario, ScenarioMutation, SimulationResult, ComparisonReport, DigitalTwin,
)
from app.simulation.digital_twin import DigitalTwinEngine


class SimulationEngine:
    """
    What-If engine: applies mutations to a Digital Twin clone,
    recalculates the decision pipeline, and produces a diff report.
    """

    @classmethod
    def simulate(cls, twin: DigitalTwin, scenario: Scenario) -> SimulationResult:
        """Run a single What-If scenario on an isolated clone."""
        # 1. Snapshot original state
        original_decision = twin.decision_report.get("decision", "UNKNOWN")
        original_risk = twin.decision_report.get("risk_level", "UNKNOWN")

        # 2. Deep-clone for isolation
        sim_twin = DigitalTwinEngine.clone_for_simulation(twin)

        # 3. Apply mutations
        for mutation in scenario.mutations:
            cls._apply_mutation(sim_twin, mutation)

        # 4. Recalculate decision on the clone
        cls._recalculate(sim_twin)

        simulated_decision = sim_twin.decision_report.get("decision", "UNKNOWN")
        simulated_risk = sim_twin.decision_report.get("risk_level", "UNKNOWN")

        # 5. Build diff
        diff = cls._compute_diff(twin, sim_twin)

        return SimulationResult(
            scenario_id=scenario.id,
            twin_id=twin.id,
            original_decision=original_decision,
            simulated_decision=simulated_decision,
            original_risk=original_risk,
            simulated_risk=simulated_risk,
            diff=diff,
            metrics={
                "decision_changed": float(original_decision != simulated_decision),
                "risk_changed": float(original_risk != simulated_risk),
            },
        )

    @classmethod
    def compare(
        cls, twin: DigitalTwin, scenario_a: Scenario, scenario_b: Scenario
    ) -> ComparisonReport:
        """Compare two scenarios side-by-side."""
        res_a = cls.simulate(twin, scenario_a)
        res_b = cls.simulate(twin, scenario_b)

        return ComparisonReport(
            scenario_a=scenario_a.name,
            scenario_b=scenario_b.name,
            results_a=res_a,
            results_b=res_b,
            diff_summary={
                "decision_a": res_a.simulated_decision,
                "decision_b": res_b.simulated_decision,
                "same_outcome": res_a.simulated_decision == res_b.simulated_decision,
            },
        )

    # ── Internal helpers ──────────────────────────────

    @classmethod
    def _apply_mutation(cls, twin: DigitalTwin, mutation: ScenarioMutation):
        """Apply a single mutation to the twin's state."""
        field = mutation.field

        # Navigate dotted paths like "validation_report.score"
        parts = field.split(".")
        target: Any = twin

        for part in parts[:-1]:
            if isinstance(target, dict):
                target = target.setdefault(part, {})
            else:
                target = getattr(target, part)

        last = parts[-1]
        if isinstance(target, dict):
            target[last] = mutation.new_value
        else:
            setattr(target, last, mutation.new_value)

    @classmethod
    def _recalculate(cls, twin: DigitalTwin):
        """
        Recalculate decision pipeline on the mutated twin.
        In a full integration this would invoke ValidationEngine + DecisionEngine.
        MVP: rule-based recalculation from the twin's own data.
        """
        val_score = twin.validation_report.get("score", 0.0)
        fraud_score = twin.metrics.get("fraud_score", 0.0)

        if fraud_score > 0.8:
            twin.decision_report["decision"] = "FRAUD_REVIEW"
            twin.decision_report["risk_level"] = "CRITICAL"
        elif val_score >= 0.95:
            twin.decision_report["decision"] = "AUTO_APPROVED"
            twin.decision_report["risk_level"] = "LOW"
        elif val_score >= 0.70:
            twin.decision_report["decision"] = "HUMAN_REVIEW"
            twin.decision_report["risk_level"] = "MEDIUM"
        else:
            twin.decision_report["decision"] = "AUTO_REJECTED"
            twin.decision_report["risk_level"] = "HIGH"

    @classmethod
    def _compute_diff(cls, original: DigitalTwin, simulated: DigitalTwin) -> Dict[str, Any]:
        """Compute a structured diff between original and simulated states."""
        diff: Dict[str, Any] = {}

        for key in ["decision", "risk_level"]:
            orig_val = original.decision_report.get(key)
            sim_val = simulated.decision_report.get(key)
            if orig_val != sim_val:
                diff[key] = {"from": orig_val, "to": sim_val}

        orig_score = original.validation_report.get("score")
        sim_score = simulated.validation_report.get("score")
        if orig_score != sim_score:
            diff["validation_score"] = {"from": orig_score, "to": sim_score}

        return diff
