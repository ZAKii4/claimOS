"""
OCR Manager to orchestrate adapters and handle fallbacks.
"""

import logging

import numpy as np

from app.engines.ocr.adapters.doctr_adapter import DocTRAdapter
from app.engines.ocr.adapters.mock_adapter import MockOCRAdapter
from app.engines.ocr.adapters.paddleocr_adapter import PaddleOCRAdapter
from app.engines.ocr.adapters.tesseract_adapter import TesseractAdapter
from app.engines.ocr.models import OCRPage

logger = logging.getLogger(__name__)


class OCRManager:
    """
    Manages OCR Adapters. Handles engine selection, fallbacks, and execution.
    """
    
    def __init__(self) -> None:
        self.adapters = {
            "doctr": DocTRAdapter(),
            "tesseract": TesseractAdapter(),
            "paddleocr": PaddleOCRAdapter(),
            "mock": MockOCRAdapter()
        }
        
    def get_available_adapters(self) -> list[str]:
        return [name for name, adapter in self.adapters.items() if adapter.is_available()]
        
    def execute(self, image: np.ndarray, engine_preference: list[str] = None) -> OCRPage:
        """
        Executes OCR trying engines in the order of engine_preference.
        If all preferred engines fail or are unavailable, falls back to MockOCRAdapter.
        """
        if not engine_preference:
            engine_preference = ["doctr", "paddleocr", "tesseract", "mock"]
            
        errors = []
            
        for engine_name in engine_preference:
            adapter = self.adapters.get(engine_name)
            if not adapter:
                errors.append(f"Engine {engine_name} is unknown.")
                continue
                
            if not adapter.is_available():
                errors.append(f"Engine {engine_name} is not available/installed.")
                continue
                
            try:
                logger.info(f"Executing OCR with {engine_name}...")
                page = adapter.process(image)
                return page
            except Exception as e:
                logger.error(f"Engine {engine_name} failed: {e}")
                errors.append(f"Engine {engine_name} failed: {str(e)}")
                
        # Ultimate fallback
        logger.warning(f"All preferred OCR engines failed. Using MockOCRAdapter. Errors: {errors}")
        return self.adapters["mock"].process(image)
