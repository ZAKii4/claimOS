"""
Exposure (Brightness, Contrast, Shadows) metrics.
"""

import cv2
import numpy as np


class ExposureAnalyzer:
    
    def analyze(self, image_gray: np.ndarray) -> dict[str, float | bool]:
        """
        Calculates brightness, contrast, and basic shadow detection.
        
        Args:
            image_gray: Grayscale OpenCV image matrix.
            
        Returns:
            Dictionary with 'contrast', 'brightness', and 'has_shadows'.
        """
        # Brightness is the mean pixel intensity (0 = black, 255 = white)
        brightness = np.mean(image_gray)
        
        # RMS Contrast is the standard deviation of pixel intensities
        contrast = np.std(image_gray)
        
        # Shadow detection heuristic: check variance in illumination across blocks
        # We divide the image into a grid and check if there's a huge discrepancy in mean brightness
        h, w = image_gray.shape
        grid_size = 4
        h_step, w_step = h // grid_size, w // grid_size
        
        block_means = []
        for i in range(grid_size):
            for j in range(grid_size):
                block = image_gray[i*h_step:(i+1)*h_step, j*w_step:(j+1)*w_step]
                block_means.append(np.mean(block))
                
        # If the brightest block and darkest block differ heavily, there might be shadows
        max_mean = max(block_means)
        min_mean = min(block_means)
        has_shadows = bool((max_mean - min_mean) > 100) # Arbitrary threshold for MVP
        
        return {
            "brightness": float(brightness),
            "contrast": float(contrast),
            "has_shadows": has_shadows
        }
