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
            # PaddleOCR 3.x renamed/removed several 2.x constructor args
            # (`use_angle_cls` -> `use_textline_orientation`, `show_log` gone
            # entirely) — this targets the 3.x API actually installed.
            self.model = PaddleOCR(use_textline_orientation=True, lang='fr')

    def process(self, image: np.ndarray) -> OCRPage:
        if not self.is_available():
            raise RuntimeError("PaddleOCR is not available.")

        self.initialize()

        start_time = time.perf_counter()

        h, w = image.shape[:2]

        # PaddleOCR 3.x replaced `.ocr()` -> [[box, (text, conf)], ...] with
        # `.predict()` -> list[OCRResult], each a dict of parallel arrays
        # (rec_texts/rec_scores/rec_polys) rather than one row per detection.
        results = self.model.predict(image)

        # PaddleOCR doesn't group by blocks or lines naturally, it returns lines/words directly.
        # We will wrap each detection in an OCRLine and OCRBlock.
        # For a true reading order reconstruction, it should be done in a post-processor.
        blocks = []

        if results:
            result = results[0]
            texts = result.get("rec_texts", [])
            scores = result.get("rec_scores", [])
            polys = result.get("rec_polys", [])
            for text, conf, poly in zip(texts, scores, polys):
                # Normalize box (Polygon is [[x1,y1], [x2,y2], [x3,y3], [x4,y4]])
                polygon = [(float(pt[0])/w, float(pt[1])/h) for pt in poly]

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
