"""
Step 10: Layout Analysis.

Takes OCR results and the page image, runs the Layout Analysis Engine,
and stores the semantic region hierarchy on each PageContext.
"""

from app.engines.base import EngineContext, EngineStatus
from app.engines.layout.manager import LayoutEngine
from app.pipeline.core import DocumentContext, ErrorSeverity, PipelineStep


class LayoutAnalysisStep(PipelineStep):

    @property
    def name(self) -> str:
        return "layout_analysis"

    def __init__(self) -> None:
        self.engine = LayoutEngine()

    def execute(self, context: DocumentContext) -> DocumentContext:
        if not context.pages:
            return context

        for page in context.pages:
            page_no = page.page_number
            ocr_result = page.engine_results.get("ocr")
            if not ocr_result or ocr_result.status != EngineStatus.SUCCESS:
                context.errors.append({
                    "step": self.name,
                    "severity": ErrorSeverity.DEGRADED,
                    "message": f"Skipped layout analysis for page {page_no}: no OCR result.",
                })
                continue

            image_path = (page.image_uri or "").replace("local://", "")

            engine_context = EngineContext(
                claim_id=context.claim_id or "00000000-0000-0000-0000-000000000000",
                input_data={
                    "image_path": image_path,
                    "ocr_result": ocr_result.output_data,
                },
            )

            result = self.engine.process(engine_context)

            if result.status == EngineStatus.SUCCESS:
                page.engine_results["layout"] = result
            else:
                context.errors.append({
                    "step": self.name,
                    "severity": ErrorSeverity.DEGRADED,
                    "message": f"Layout analysis failed on page {page_no}: {result.errors}",
                })

        return context
