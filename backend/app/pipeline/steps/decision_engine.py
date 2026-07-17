"""
Step 15: Decision Engine.

Runs the Decision Engine against the ValidationReport and Evidence Graph to
compute the final routing decision (ValidationDecision) for the claim.
"""

from app.engines.base import EngineContext, EngineStatus
from app.engines.decision.manager import DecisionEngine
from app.pipeline.core import DocumentContext, ErrorSeverity, PipelineStep


class DecisionEngineStep(PipelineStep):

    @property
    def name(self) -> str:
        return "decision_engine"

    def __init__(self) -> None:
        self.engine = DecisionEngine()

    def execute(self, context: DocumentContext) -> DocumentContext:
        validation_result = context.engine_results.get("validation")
        evidence_graph_result = context.engine_results.get("evidence_graph")

        if not validation_result or validation_result.status != EngineStatus.SUCCESS:
            context.errors.append({
                "step": self.name,
                "severity": ErrorSeverity.DEGRADED,
                "message": "Skipped decision engine: no successful validation report available.",
            })
            context.validation_decision = "HITL_REVIEW"
            return context

        if not evidence_graph_result or evidence_graph_result.status != EngineStatus.SUCCESS:
            context.errors.append({
                "step": self.name,
                "severity": ErrorSeverity.DEGRADED,
                "message": "Skipped decision engine: no successful evidence graph result.",
            })
            context.validation_decision = "HITL_REVIEW"
            return context

        engine_context = EngineContext(
            claim_id=context.claim_id or "00000000-0000-0000-0000-000000000000",
            input_data={
                "validation_report": validation_result.output_data.get("validation_report"),
                "evidence_graph_result": evidence_graph_result.output_data.get(
                    "evidence_graph_result"
                ),
            },
        )

        result = self.engine.process(engine_context)

        if result.status == EngineStatus.SUCCESS:
            context.engine_results["decision"] = result
            decision_data = result.output_data.get("decision_result", {})
            context.validation_decision = decision_data.get("decision")
        else:
            context.errors.append({
                "step": self.name,
                "severity": ErrorSeverity.DEGRADED,
                "message": f"Decision engine failed: {result.errors}. Defaulting to human review.",
            })
            context.validation_decision = "HITL_REVIEW"

        return context
