"""
Step 13: Evidence Graph.

Takes the Extraction results and runs the Evidence Graph Engine, building
the document's Knowledge Graph (entities + relationships) on the
DocumentContext.

Note: like the Classification/Extraction engines it feeds from, this
operates on a single logical document per claim (the current architecture's
documented single-page-document limitation, not introduced here).
"""

from app.engines.base import EngineContext, EngineStatus
from app.engines.evidence_graph.manager import EvidenceGraphEngine
from app.pipeline.core import DocumentContext, ErrorSeverity, PipelineStep


class EvidenceGraphStep(PipelineStep):

    @property
    def name(self) -> str:
        return "evidence_graph"

    def __init__(self) -> None:
        self.engine = EvidenceGraphEngine()

    def execute(self, context: DocumentContext) -> DocumentContext:
        extraction_result = None
        for page in context.pages:
            result = page.engine_results.get("extraction")
            if result and result.status == EngineStatus.SUCCESS:
                extraction_result = result.output_data.get("extraction_result")
                break

        if not extraction_result:
            context.errors.append({
                "step": self.name,
                "severity": ErrorSeverity.DEGRADED,
                "message": "Skipped evidence graph: no successful extraction result available.",
            })
            return context

        engine_context = EngineContext(
            claim_id=context.claim_id or "00000000-0000-0000-0000-000000000000",
            input_data={"extraction_result": extraction_result},
        )

        result = self.engine.process(engine_context)

        if result.status == EngineStatus.SUCCESS:
            context.engine_results["evidence_graph"] = result
        else:
            context.errors.append({
                "step": self.name,
                "severity": ErrorSeverity.DEGRADED,
                "message": f"Evidence graph construction failed: {result.errors}",
            })

        return context
