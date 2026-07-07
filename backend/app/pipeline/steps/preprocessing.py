"""
Step 08: Preprocessing.

Performs deskew, binarization, and noise reduction on extracted page images.
"""

import os

from app.engines.base import EngineContext, EngineStatus
from app.engines.preprocessing.engine import AdaptivePreprocessingEngine
from app.pipeline.core import DocumentContext, ErrorSeverity, PipelineStep


class PreprocessingStep(PipelineStep):
    
    @property
    def name(self) -> str:
        return "preprocessing"

    def __init__(self) -> None:
        self.engine = AdaptivePreprocessingEngine()

    def execute(self, context: DocumentContext) -> DocumentContext:
        if not context.pages:
            return context
            
        output_dir = os.path.dirname(context.storage_uri.replace("local://", "")) if context.storage_uri else "/tmp"
            
        for page in context.pages:
            if not page.image_uri:
                continue
                
            iqa_report_result = page.engine_results.get("iqa")
            if not iqa_report_result or iqa_report_result.status != EngineStatus.SUCCESS:
                # Without IQA, we cannot adaptively preprocess. Fallback to just passing the image.
                context.errors.append({
                    "step": self.name,
                    "severity": ErrorSeverity.DEGRADED,
                    "message": f"Skipped preprocessing for page {page.page_number} due to missing IQA report."
                })
                continue
                
            image_path = page.image_uri.replace("local://", "")
            
            engine_context = EngineContext(
                claim_id=context.claim_id or "00000000-0000-0000-0000-000000000000",
                input_data={
                    "image_path": image_path,
                    "iqa_report": iqa_report_result.output_data,
                    "output_dir": output_dir
                }
            )
            
            result = self.engine.process(engine_context)
            
            if result.status == EngineStatus.SUCCESS:
                page.engine_results["preprocessing"] = result
                # Update the page's image URI to the newly optimized image!
                new_image_path = result.output_data.get("output_image_path")
                if new_image_path:
                    page.image_uri = f"local://{new_image_path}"
            else:
                context.errors.append({
                    "step": self.name,
                    "severity": ErrorSeverity.DEGRADED,
                    "message": f"Preprocessing failed on page {page.page_number}: {result.errors}"
                })
                
        return context
