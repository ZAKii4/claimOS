from typing import Optional
import numpy as np

from app.engines.layout.base import BaseDetector
from app.engines.layout.models import HeaderRegion, LayoutRegion
from app.engines.ocr.models import OCRPage


class HeaderDetector(BaseDetector):
    @property
    def name(self) -> str:
        return "header_detector"

    def detect(self, image: np.ndarray, ocr_page: Optional[OCRPage] = None) -> list[LayoutRegion]:
        if not ocr_page:
            return []

        regions = []
        
        # Heuristic: Find blocks that are at the very top or bottom of the page, 
        # or blocks that have only 1-2 lines and are centered.
        # Here we do a simple extraction of the topmost text blocks.
        
        for block in ocr_page.blocks:
            # Check if it's in the top 10% of the page
            if block.bbox.y_max < 0.10:
                text = "\n".join(" ".join(w.text for w in line.words) for line in block.lines)
                
                region = HeaderRegion(
                    bounding_box=block.bbox,
                    text=text,
                    level=1,
                    associated_lines=block.lines,
                    associated_words=[w for line in block.lines for w in line.words]
                )
                regions.append(region)
                
        return regions
