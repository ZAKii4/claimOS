import cv2
import numpy as np
from typing import Optional

from app.engines.layout.base import BaseDetector
from app.engines.layout.models import LayoutRegion, CheckboxRegion
from app.engines.ocr.models import BoundingBox, OCRPage


class CheckboxDetector(BaseDetector):
    @property
    def name(self) -> str:
        return "checkbox_detector"

    def detect(self, image: np.ndarray, ocr_page: Optional[OCRPage] = None) -> list[LayoutRegion]:
        regions = []
        
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        h, w = image.shape[:2]
        
        for c in contours:
            x, y, cw, ch = cv2.boundingRect(c)
            
            # Checkboxes are usually small squares
            aspect_ratio = float(cw) / ch
            if 10 <= cw <= 40 and 10 <= ch <= 40 and 0.8 <= aspect_ratio <= 1.2:
                # To check if it's checked, compute fill ratio
                roi = thresh[y:y+ch, x:x+cw]
                fill_ratio = cv2.countNonZero(roi) / (cw * ch)
                
                # A box border has some fill, a cross inside increases it
                is_checked = fill_ratio > 0.4
                
                cb = CheckboxRegion(
                    bounding_box=BoundingBox(
                        x_min=x / w,
                        y_min=y / h,
                        x_max=(x + cw) / w,
                        y_max=(y + ch) / h
                    ),
                    is_checked=is_checked,
                    checkbox_type="box"
                )
                regions.append(cb)
                
        return regions
