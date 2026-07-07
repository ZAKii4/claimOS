"""
Exposure operations: CLAHE, Shadow Removal.
"""

from typing import Any

import cv2
import numpy as np

from app.engines.preprocessing.operations.base import BaseOperation


class CLAHEOperation(BaseOperation):
    
    def __init__(self, clip_limit: float = 2.0, tile_grid_size: tuple[int, int] = (8, 8)) -> None:
        self.clip_limit = clip_limit
        self.tile_grid_size = tile_grid_size

    @property
    def name(self) -> str:
        return "clahe"

    def process(self, image: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
        # CLAHE operates on grayscale or the L channel of LAB color space
        is_color = len(image.shape) == 3
        clahe = cv2.createCLAHE(clipLimit=self.clip_limit, tileGridSize=self.tile_grid_size)
        
        if is_color:
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            cl = clahe.apply(l)
            limg = cv2.merge((cl, a, b))
            final_img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        else:
            final_img = clahe.apply(image)
            
        return final_img, {"clip_limit": self.clip_limit, "tile_grid_size": self.tile_grid_size}


class ShadowRemovalOperation(BaseOperation):
    
    @property
    def name(self) -> str:
        return "shadow_removal"

    def process(self, image: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
        # Divide image by a heavily dilated/blurred version of itself to normalize illumination
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        # Dilate to remove text but keep the background shading
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))
        bg = cv2.dilate(gray, kernel)
        
        # Apply median blur to smooth out the background estimate
        bg = cv2.medianBlur(bg, 21)
        
        # Divide original image by the background
        diff = 255 - cv2.absdiff(gray, bg)
        
        # Normalize
        norm = cv2.normalize(diff, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
        
        # If original was color, we might want to return grayscale anyway for OCR, 
        # but to keep it strictly color if it was, we just return the normalized gray as 3 channel
        if len(image.shape) == 3:
            final_img = cv2.cvtColor(norm, cv2.COLOR_GRAY2BGR)
        else:
            final_img = norm
            
        return final_img, {"method": "dilation_division"}
