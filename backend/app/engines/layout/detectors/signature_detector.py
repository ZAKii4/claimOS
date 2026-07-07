import cv2
import numpy as np
from typing import Optional

from app.engines.layout.base import BaseDetector
from app.engines.layout.models import LayoutRegion, SignatureRegion
from app.engines.ocr.models import BoundingBox, OCRPage


class SignatureDetector(BaseDetector):
    @property
    def name(self) -> str:
        return "signature_detector"

    def detect(self, image: np.ndarray, ocr_page: Optional[OCRPage] = None) -> list[LayoutRegion]:
        regions = []
        
        # Placeholder for real signature detection.
        # A real implementation could use:
        # 1. A YOLOv8 model trained on signature bounding boxes.
        # 2. Heuristics finding blue ink pixels or isolated high-density non-text strokes.
        
        # Let's mock a detection if we find a blue-ish stroke (very simplified)
        # Convert to HSV to find blue ink
        if len(image.shape) == 3:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            lower_blue = np.array([100, 50, 50])
            upper_blue = np.array([130, 255, 255])
            
            mask = cv2.inRange(hsv, lower_blue, upper_blue)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            h, w = image.shape[:2]
            
            for c in contours:
                x, y, cw, ch = cv2.boundingRect(c)
                # Ensure it has a certain size to be a signature
                if cw > 50 and ch > 20:
                    sig = SignatureRegion(
                        bounding_box=BoundingBox(
                            x_min=x / w,
                            y_min=y / h,
                            x_max=(x + cw) / w,
                            y_max=(y + ch) / h
                        ),
                        is_handwritten=True,
                        confidence=0.8
                    )
                    regions.append(sig)
                    
        return regions
