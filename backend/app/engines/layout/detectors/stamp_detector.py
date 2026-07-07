import cv2
import numpy as np
from typing import Optional

from app.engines.layout.base import BaseDetector
from app.engines.layout.models import LayoutRegion, StampRegion
from app.engines.ocr.models import BoundingBox, OCRPage


class StampDetector(BaseDetector):
    @property
    def name(self) -> str:
        return "stamp_detector"

    def detect(self, image: np.ndarray, ocr_page: Optional[OCRPage] = None) -> list[LayoutRegion]:
        regions = []
        
        # Stamps are often circular or heavily bordered rectangles.
        # Let's mock a Hough Circle transform to find circular stamps.
        
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        # Blur to reduce noise
        gray_blurred = cv2.medianBlur(gray, 5)
        
        circles = cv2.HoughCircles(
            gray_blurred, 
            cv2.HOUGH_GRADIENT, 
            dp=1, 
            minDist=50, 
            param1=50, 
            param2=30, 
            minRadius=20, 
            maxRadius=150
        )
        
        h, w = image.shape[:2]
        
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for i in circles[0, :]:
                cx, cy, r = i[0], i[1], i[2]
                
                stamp = StampRegion(
                    bounding_box=BoundingBox(
                        x_min=max(0, (cx - r)) / w,
                        y_min=max(0, (cy - r)) / h,
                        x_max=min(w, (cx + r)) / w,
                        y_max=min(h, (cy + r)) / h
                    ),
                    shape="circular",
                    confidence=0.7
                )
                regions.append(stamp)
                
        return regions
