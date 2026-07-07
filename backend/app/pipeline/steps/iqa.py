"""
Step 07.5: Image Quality Assessment (IQA).

Analyzes the quality of extracted pages before preprocessing.
Routes bad pages for review, or provides metadata for adaptive preprocessing.
"""

from app.engines.base import EngineContext, EngineStatus
from app.engines.iqa.engine import IQAEngine
from app.pipeline.core import DocumentContext, ErrorSeverity, PipelineError, PipelineStep


class IQAAssessmentStep(PipelineStep):
    
    @property
    def name(self) -> str:
        return "iqa_assessment"

    def __init__(self) -> None:
        self.engine = IQAEngine()

    def execute(self, context: DocumentContext) -> DocumentContext:
        if not context.pages:
            # Nothing to analyze
            return context
            
        for page in context.pages:
            if not page.image_uri:
                continue
                
            # Convert URI to local path (assuming local storage for MVP)
            image_path = page.image_uri.replace("local://", "")
            
            engine_context = EngineContext(
                claim_id=context.claim_id or "00000000-0000-0000-0000-000000000000",
                input_data={"image_path": image_path}
            )
            
            result = self.engine.process(engine_context)
            
            if result.status == EngineStatus.FAILURE:
                # We do not fail the whole pipeline just because IQA failed on one page,
                # we just record a DEGRADED error and move on.
                context.errors.append({
                    "step": self.name,
                    "severity": ErrorSeverity.DEGRADED,
                    "message": f"IQA failed on page {page.page_number}: {result.errors}"
                })
            else:
                page.engine_results["iqa"] = result
                
        return context
