from typing import Optional
import numpy as np

from app.engines.layout.base import BaseDetector
from app.engines.layout.models import LayoutRegion, ParagraphRegion
from app.engines.ocr.models import OCRPage


class ParagraphDetector(BaseDetector):
    @property
    def name(self) -> str:
        return "paragraph_detector"

    def detect(self, image: np.ndarray, ocr_page: Optional[OCRPage] = None) -> list[LayoutRegion]:
        if not ocr_page:
            return []

        regions = []
        
        # Simple heuristic: treat each OCRBlock as a paragraph.
        # A more advanced version would use DBSCAN on OCRLines.
        for block in ocr_page.blocks:
            text = "\n".join(" ".join(w.text for w in line.words) for line in block.lines)
            
            # Filter out very short blocks that might be headers, though this can be refined later.
            region = ParagraphRegion(
                bounding_box=block.bbox,
                text=text,
                associated_lines=block.lines,
                associated_words=[w for line in block.lines for w in line.words],
                confidence=1.0  # Trust OCR structure for now
            )
            regions.append(region)
            
        return regions
