"""
Noise analysis metrics.
"""

import cv2
import numpy as np


class NoiseAnalyzer:
    
    def analyze(self, image_gray: np.ndarray) -> dict[str, float]:
        """
        Estimates the noise level in the image.
        Approaches this by applying a median blur and measuring the 
        difference/variance between the original and blurred image.
        
        Args:
            image_gray: Grayscale OpenCV image matrix.
            
        Returns:
            Dictionary with 'noise_level'.
        """
        # Apply median blur to smooth out noise
        blurred = cv2.medianBlur(image_gray, 3)
        
        # Calculate the absolute difference between original and blurred
        diff = cv2.absdiff(image_gray, blurred)
        
        # Calculate the mean of the difference. Higher mean -> more noise.
        # Normalize to a 0.0 - 1.0 scale (roughly, mean difference / 255.0)
        noise_level = np.mean(diff) / 255.0
        
        return {
            "noise_level": float(noise_level)
        }
