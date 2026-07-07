"""
Blur and Focus analysis metrics.
"""

import cv2
import numpy as np


class BlurAnalyzer:
    
    def __init__(self, blur_threshold: float = 100.0) -> None:
        """
        Args:
            blur_threshold: Variance of Laplacian below this value is considered blurred.
                            100.0 is a standard empirical threshold for text documents.
        """
        self.blur_threshold = blur_threshold

    def analyze(self, image_gray: np.ndarray) -> dict[str, float | bool]:
        """
        Calculates the Variance of Laplacian to estimate blur.
        
        Args:
            image_gray: Grayscale OpenCV image matrix.
            
        Returns:
            Dictionary with 'blur_level' and 'is_blurred'.
        """
        variance = cv2.Laplacian(image_gray, cv2.CV_64F).var()
        
        return {
            "blur_level": float(variance),
            "is_blurred": bool(variance < self.blur_threshold)
        }
