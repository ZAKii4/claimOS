import cv2
import numpy as np
from typing import Optional

from app.engines.layout.base import BaseDetector
from app.engines.layout.models import LayoutRegion, TableRegion, TableRow, TableColumn, TableCell
from app.engines.ocr.models import BoundingBox, OCRPage


class TableDetector(BaseDetector):
    @property
    def name(self) -> str:
        return "table_detector"

    def detect(self, image: np.ndarray, ocr_page: Optional[OCRPage] = None) -> list[LayoutRegion]:
        regions = []
        
        # 1. Convert to grayscale if not already
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        # 2. Thresholding
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        
        # 3. Detect horizontal and vertical lines using morphology
        kernel_length = np.array(gray).shape[1] // 40
        vert_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_length))
        hori_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_length, 1))
        
        # Vertical lines
        img_temp1 = cv2.erode(thresh, vert_kernel, iterations=1)
        vert_lines_img = cv2.dilate(img_temp1, vert_kernel, iterations=1)
        
        # Horizontal lines
        img_temp2 = cv2.erode(thresh, hori_kernel, iterations=1)
        hori_lines_img = cv2.dilate(img_temp2, hori_kernel, iterations=1)
        
        # 4. Combine and find contours
        alpha = 0.5
        beta = 0.5 - alpha
        img_final_bin = cv2.addWeighted(vert_lines_img, alpha, hori_lines_img, beta, 0.0)
        _, img_final_bin = cv2.threshold(img_final_bin, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        
        contours, _ = cv2.findContours(img_final_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        h, w = image.shape[:2]
        
        for c in contours:
            x, y, cw, ch = cv2.boundingRect(c)
            # Filter out very small boxes or boxes that take up the whole page
            if (cw > 100 and ch > 100) and (cw < w * 0.95 or ch < h * 0.95):
                # We found a potential table
                table = TableRegion(
                    bounding_box=BoundingBox(
                        x_min=x / w,
                        y_min=y / h,
                        x_max=(x + cw) / w,
                        y_max=(y + ch) / h
                    )
                )
                regions.append(table)
                
                # In a real implementation, we would extract cells using internal contours
                # and align OCR words to the cells.
                
        return regions
