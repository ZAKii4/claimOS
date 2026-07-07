"""
PaddleOCR Adapter.
"""

import time
import logging

import numpy as np

from app.engines.ocr.base import BaseOCRAdapter
from app.engines.ocr.models import BoundingBox, OCRBlock, OCRLine, OCRPage, OCRWord

logger = logging.getLogger(__name__)

try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False


class PaddleOCRAdapter(BaseOCRAdapter):
    
    def __init__(self) -> None:
        self.model = None

    @property
    def name(self) -> str:
        return "paddleocr"
        
    @property
    def version(self) -> str:
        try:
            import paddleocr
            return paddleocr.__version__
        except ImportError:
            return "unknown"

    def is_available(self) -> bool:
        return PADDLE_AVAILABLE

    def initialize(self) -> None:
        if not self.is_available():
            raise RuntimeError("PaddleOCR is not installed.")
        if self.model is None:
            # We initialize with French by default. This could be dynamic.
            self.model = PaddleOCR(use_angle_cls=True, lang='fr', show_log=False)

    def process(self, image: np.ndarray) -> OCRPage:
        if not self.is_available():
            raise RuntimeError("PaddleOCR is not available.")
            
        self.initialize()
        
        start_time = time.perf_counter()
        
        h, w = image.shape[:2]
        
        # Output format: [[[[x,y], [x,y], [x,y], [x,y]], ('text', confidence)], ...]
        result = self.model.ocr(image, cls=True)
        
        # PaddleOCR doesn't group by blocks or lines naturally, it returns lines/words directly.
        # We will wrap each detection in an OCRLine and OCRBlock.
        # For a true reading order reconstruction, it should be done in a post-processor.
        blocks = []
        
        if result and result[0]:
            for line_res in result[0]:
                box, (text, conf) = line_res
                
                # Normalize box (Polygon is [[x1,y1], [x2,y2], [x3,y3], [x4,y4]])
                polygon = [(float(pt[0])/w, float(pt[1])/h) for pt in box]
                
                x_coords = [p[0] for p in polygon]
                y_coords = [p[1] for p in polygon]
                x_min, x_max = max(0.0, min(x_coords)), min(1.0, max(x_coords))
                y_min, y_max = max(0.0, min(y_coords)), min(1.0, max(y_coords))
                
                bbox = BoundingBox(x_min=x_min, y_min=y_min, x_max=x_max, y_max=y_max)
                
                word = OCRWord(
                    text=text,
                    confidence=float(conf),
                    bbox=bbox,
                    polygon=polygon,
                    language="fr",
                    engine_name=self.name
                )
                
                ocr_line = OCRLine(words=[word], bbox=bbox)
                blocks.append(OCRBlock(lines=[ocr_line], bbox=bbox))
                
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        
        return OCRPage(
            blocks=blocks,
            language="fr",
            engine_name=self.name,
            processing_time_ms=elapsed_ms
        )
