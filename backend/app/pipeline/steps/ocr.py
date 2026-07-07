"""
OCR Pipeline Step.
Orchestrates the Hybrid OCR Engine to extract text, bounding boxes, and metadata
for each page.
"""

import os

from app.engines.base import EngineContext, EngineStatus
from app.engines.ocr.engine import HybridOCREngine
from app.pipeline.core import DocumentContext, ErrorSeverity, PipelineStep


class OCRStep(PipelineStep):
    
    @property
    def name(self) -> str:
        return "ocr"
        
    def __init__(self) -> None:
        self.engine = HybridOCREngine()

    def execute(self, context: DocumentContext) -> DocumentContext:
        if not context.pages:
            return context
            
        for page in context.pages:
            if not page.image_uri:
                context.errors.append({
                    "step": self.name,
                    "severity": ErrorSeverity.FATAL,
                    "message": f"No image URI found for page {page.page_number}."
                })
                continue
                
            image_path = page.image_uri.replace("local://", "")
            
            # Fetch IQA report if it exists to pass to Confidence Engine
            iqa_report = {}
            if "iqa" in page.engine_results and page.engine_results["iqa"].status == EngineStatus.SUCCESS:
                iqa_report = page.engine_results["iqa"].output_data
                
            engine_context = EngineContext(
                claim_id=context.claim_id or "00000000-0000-0000-0000-000000000000",
                input_data={
                    "image_path": image_path,
                    "iqa_report": iqa_report,
                    # We can specify engine preference here. For tests, we can default to ["tesseract", "mock"]
                    "engine_preference": ["tesseract", "mock"]
                }
            )
            
            result = self.engine.process(engine_context)
            
            if result.status == EngineStatus.SUCCESS:
                page.engine_results["ocr"] = result
            else:
                context.errors.append({
                    "step": self.name,
                    "severity": ErrorSeverity.FATAL,
                    "message": f"OCR Engine failed on page {page.page_number}: {result.errors}"
                })
                
        return context
