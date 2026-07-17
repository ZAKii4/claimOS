"""
Hybrid OCR Engine implementation.
"""

import os

import cv2

from app.engines.base import BaseEngine, EngineContext, EngineResult, EngineStatus
from app.engines.ocr.confidence import ConfidenceEngine
from app.engines.ocr.manager import OCRManager
from app.engines.ocr.models import OCRResult
from app.engines.ocr.postprocessing import PostProcessingEngine
from app.engines.ocr.reading_order import ReadingOrderEngine
from app.engines.ocr.visualization import OCRVisualizer


class HybridOCREngine(BaseEngine):
    """
    Main entry point for the OCR Phase.
    Orchestrates the OCRManager, PostProcessing, ReadingOrder, and Confidence calculations.
    """

    def __init__(self) -> None:
        self.manager = OCRManager()
        self.reading_order = ReadingOrderEngine()
        self.post_processor = PostProcessingEngine()
        self.confidence_engine = ConfidenceEngine()
        self.visualizer = OCRVisualizer()

    @property
    def name(self) -> str:
        return "hybrid_ocr"

    @property
    def version(self) -> str:
        return "1.0.0"

    def process(self, context: EngineContext) -> EngineResult:
        """
        Expects:
            context.input_data["image_path"]: str
            context.input_data["iqa_report"]: dict
            context.input_data["engine_preference"]: list[str] (Optional)
        """
        image_path = context.input_data.get("image_path")
        iqa_report = context.input_data.get("iqa_report", {})
        engine_preference = context.input_data.get("engine_preference")

        if not image_path or not os.path.exists(image_path):
            return self._fail(f"Invalid image_path: {image_path}")

        image = cv2.imread(image_path)
        if image is None:
            return self._fail("Failed to decode image.")

        # 1. Execute OCR
        try:
            ocr_page = self.manager.execute(image, engine_preference=engine_preference)
        except Exception as e:
            return self._fail(f"OCR Execution failed: {str(e)}")

        # 2. Reconstruct Reading Order
        ocr_page = self.reading_order.reconstruct(ocr_page)

        # 3. Post Processing (Clean text)
        ocr_page = self.post_processor.clean(ocr_page)

        # 4. Confidence Calculation
        final_confidence = self.confidence_engine.calculate_score(ocr_page, iqa_report)

        # Build Final Result
        detected_languages = {
            word.language
            for block in ocr_page.blocks
            for line in block.lines
            for word in line.words
            if word.language
        }
        result = OCRResult(
            page=ocr_page,
            confidence_score=final_confidence,
            is_multilingual=len(detected_languages) > 1
        )

        # Optional: Save visualization if requested
        if context.input_data.get("save_visualization"):
            viz = self.visualizer.draw(image, ocr_page)
            viz_path = image_path.replace(".png", "_ocr_viz.png").replace(".jpg", "_ocr_viz.jpg")
            cv2.imwrite(viz_path, viz)
            # You could add viz_path to the output_data if needed

        return EngineResult(
            engine_name=self.name,
            engine_version=self.version,
            status=EngineStatus.SUCCESS,
            output_data=result.model_dump(),
            processing_time_ms=ocr_page.processing_time_ms
        )

    def _fail(self, message: str) -> EngineResult:
        return EngineResult(
            engine_name=self.name,
            engine_version=self.version,
            status=EngineStatus.FAILURE,
            errors=[message]
        )

    def health_check(self) -> bool:
        return True
