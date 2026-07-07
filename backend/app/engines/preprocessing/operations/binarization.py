"""
Binarization operations: Adaptive Thresholding, Sauvola.
"""

from typing import Any

import cv2
import numpy as np
from skimage.filters import threshold_sauvola

from app.engines.preprocessing.operations.base import BaseOperation


class AdaptiveThresholdOperation(BaseOperation):
    
    def __init__(self, block_size: int = 15, c: int = 10) -> None:
        self.block_size = block_size
        self.c = c

    @property
    def name(self) -> str:
        return "binarize_adaptive"

    def process(self, image: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
        # Requires grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,
            self.block_size, self.c
        )
        
        return binary, {"block_size": self.block_size, "c": self.c}


class SauvolaBinarization(BaseOperation):
    
    def __init__(self, window_size: int = 25, k: float = 0.2) -> None:
        self.window_size = window_size
        self.k = k

    @property
    def name(self) -> str:
        return "binarize_sauvola"

    def process(self, image: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
        # Sauvola is fantastic for degraded documents with non-uniform illumination.
        # It's slower than OpenCV's adaptiveThreshold but much higher quality.
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        # Scikit-image sauvola
        thresh_sauvola = threshold_sauvola(gray, window_size=self.window_size, k=self.k)
        
        # Create binary mask (numpy vectorized operation)
        binary = (gray > thresh_sauvola) * 255
        binary = binary.astype(np.uint8)
        
        return binary, {"window_size": self.window_size, "k": self.k}
