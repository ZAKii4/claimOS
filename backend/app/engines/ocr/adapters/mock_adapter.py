"""
Mock OCR Adapter for MVP and Unit Testing.
Provides predictable outputs without requiring heavy ML libraries like PyTorch or Tesseract.
"""

import time

import numpy as np

from app.engines.ocr.base import BaseOCRAdapter
from app.engines.ocr.models import BoundingBox, OCRBlock, OCRLine, OCRPage, OCRWord


class MockOCRAdapter(BaseOCRAdapter):
    
    @property
    def name(self) -> str:
        return "mock_ocr"
        
    @property
    def version(self) -> str:
        return "1.0.0"

    def initialize(self) -> None:
        pass

    def is_available(self) -> bool:
        return True

    def process(self, image: np.ndarray) -> OCRPage:
        start_time = time.perf_counter()
        
        # We just generate a fake page with some words
        # In a real scenario, this would execute PyTorch model inference
        word1 = OCRWord(
            text="SYNTHETIC",
            confidence=0.99,
            bbox=BoundingBox(x_min=0.1, y_min=0.1, x_max=0.3, y_max=0.15),
            polygon=[(0.1, 0.1), (0.3, 0.1), (0.3, 0.15), (0.1, 0.15)],
            language="en",
            engine_name=self.name
        )
        
        word2 = OCRWord(
            text="DATA",
            confidence=0.95,
            bbox=BoundingBox(x_min=0.31, y_min=0.1, x_max=0.45, y_max=0.15),
            polygon=[(0.31, 0.1), (0.45, 0.1), (0.45, 0.15), (0.31, 0.15)],
            language="en",
            engine_name=self.name
        )
        
        line = OCRLine(
            words=[word1, word2],
            bbox=BoundingBox(x_min=0.1, y_min=0.1, x_max=0.45, y_max=0.15)
        )
        
        block = OCRBlock(
            lines=[line],
            bbox=BoundingBox(x_min=0.1, y_min=0.1, x_max=0.45, y_max=0.15)
        )
        
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        
        return OCRPage(
            blocks=[block],
            language="en",
            engine_name=self.name,
            processing_time_ms=elapsed_ms
        )
