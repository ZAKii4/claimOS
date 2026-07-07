"""
Filters: Denoising, Sharpening, Morphological Operations.
"""

from typing import Any

import cv2
import numpy as np

from app.engines.preprocessing.operations.base import BaseOperation


class MedianBlurDenoise(BaseOperation):
    
    def __init__(self, kernel_size: int = 3) -> None:
        self.kernel_size = kernel_size

    @property
    def name(self) -> str:
        return "denoise_median"

    def process(self, image: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
        denoised = cv2.medianBlur(image, self.kernel_size)
        return denoised, {"kernel_size": self.kernel_size}


class NonLocalMeansDenoise(BaseOperation):
    
    @property
    def name(self) -> str:
        return "denoise_nlmeans"

    def process(self, image: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
        # Non-Local Means is computationally expensive but excellent for retaining text edges
        if len(image.shape) == 3:
            denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        else:
            denoised = cv2.fastNlMeansDenoising(image, None, 10, 7, 21)
            
        return denoised, {"h": 10, "templateWindowSize": 7, "searchWindowSize": 21}


class SharpeningOperation(BaseOperation):
    
    @property
    def name(self) -> str:
        return "sharpen"

    def process(self, image: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
        # Unsharp Mask technique
        gaussian = cv2.GaussianBlur(image, (9, 9), 10.0)
        sharpened = cv2.addWeighted(image, 1.5, gaussian, -0.5, 0)
        return sharpened, {"method": "unsharp_mask", "sigma": 10.0}


class MorphologicalOpening(BaseOperation):
    
    def __init__(self, kernel_size: int = 2) -> None:
        self.kernel_size = kernel_size

    @property
    def name(self) -> str:
        return "morph_opening"

    def process(self, image: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
        # Useful for removing tiny noise specs after binarization
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (self.kernel_size, self.kernel_size))
        # Note: In standard OCR binarization, text is black, background is white.
        # Morphological opening on a white background with black text actually erodes the background
        # and dilates the black text (thickens it). 
        # But if the image is inverted (black background, white text), it removes small white noise.
        # We assume standard orientation here (white background).
        opened = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        return opened, {"kernel_size": self.kernel_size, "shape": "RECT"}
