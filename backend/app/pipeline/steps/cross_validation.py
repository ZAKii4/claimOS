"""
Step 14: Cross-Validation.

Runs the Validation Rule Engine against the Evidence Graph (and raw
extraction data) to detect contradictions/discrepancies and produce a
ValidationReport on the DocumentContext.
"""

from app.engines.base import EngineContext, EngineStatus
from app.engines.validation.manager import ValidationEngine
from app.pipeline.core import DocumentContext, ErrorSeverity, PipelineStep


class CrossValidationStep(PipelineStep):

    @property
    def name(self) -> str:
        return "cross_validation"

    def __init__(self) -> None:
        self.engine = ValidationEngine()

    def execute(self, context: DocumentContext) -> DocumentContext:
        evidence_graph_result = context.engine_results.get("evidence_graph")

        if not evidence_graph_result or evidence_graph_result.status != EngineStatus.SUCCESS:
            context.errors.append({
                "step": self.name,
                "severity": ErrorSeverity.DEGRADED,
                "message": "Skipped cross-validation: no successful evidence graph result.",
            })
            return context

        graph_data = evidence_graph_result.output_data.get("evidence_graph_result")
        engine_context = EngineContext(
            claim_id=context.claim_id or "00000000-0000-0000-0000-000000000000",
            input_data={
                "evidence_graph_result": graph_data,
                "extraction_result": context.extracted_data,
            },
        )

        result = self.engine.process(engine_context)

        if result.status == EngineStatus.SUCCESS:
            context.engine_results["validation"] = result
        else:
            context.errors.append({
                "step": self.name,
                "severity": ErrorSeverity.DEGRADED,
                "message": f"Cross-validation failed: {result.errors}",
            })

        return context
