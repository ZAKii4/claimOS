"""
Step 11: Classification.

Takes OCR and Layout results, runs the Intelligent Document Classification
Engine, and records the predicted document class on each PageContext.
"""

from app.engines.base import EngineContext, EngineStatus
from app.engines.classification.manager import ClassificationEngine
from app.pipeline.core import DocumentContext, ErrorSeverity, PipelineStep


class ClassificationStep(PipelineStep):

    @property
    def name(self) -> str:
        return "classification"

    def __init__(self) -> None:
        self.engine = ClassificationEngine()

    def execute(self, context: DocumentContext) -> DocumentContext:
        if not context.pages:
            return context

        for page in context.pages:
            ocr_result = page.engine_results.get("ocr")
            layout_result = page.engine_results.get("layout")

            page_no = page.page_number
            if not ocr_result or ocr_result.status != EngineStatus.SUCCESS:
                context.errors.append({
                    "step": self.name,
                    "severity": ErrorSeverity.DEGRADED,
                    "message": f"Skipped classification for page {page_no}: no OCR result.",
                })
                continue

            if not layout_result or layout_result.status != EngineStatus.SUCCESS:
                context.errors.append({
                    "step": self.name,
                    "severity": ErrorSeverity.DEGRADED,
                    "message": f"Skipped classification for page {page_no}: no layout result.",
                })
                continue

            engine_context = EngineContext(
                claim_id=context.claim_id or "00000000-0000-0000-0000-000000000000",
                input_data={
                    "ocr_result": ocr_result.output_data,
                    "layout_result": layout_result.output_data.get("layout_analysis_result"),
                },
            )

            result = self.engine.process(engine_context)

            if result.status == EngineStatus.SUCCESS:
                page.engine_results["classification"] = result
                classification_result = result.output_data.get("classification_result", {})
                documents = classification_result.get("documents") or []
                if documents and not context.document_type_code:
                    document_class = (
                        documents[0].get("classification", {}).get("document_class") or {}
                    )
                    context.document_type_code = document_class.get("family")
            else:
                context.errors.append({
                    "step": self.name,
                    "severity": ErrorSeverity.DEGRADED,
                    "message": f"Classification failed on page {page.page_number}: {result.errors}",
                })

        return context
