"""
Content heuristics (Stamps, Text Density).
"""

import cv2
import numpy as np


class ContentAnalyzer:
    
    def analyze(self, image_color: np.ndarray, image_gray: np.ndarray) -> dict[str, float | bool]:
        """
        Applies OpenCV heuristics to estimate text density and presence of stamps.
        For MVP, we avoid heavy ML models and use color/thresholding logic.
        
        Args:
            image_color: BGR OpenCV image matrix.
            image_gray: Grayscale OpenCV image matrix.
            
        Returns:
            Dictionary with 'text_density', 'has_stamps', 'has_signatures', 'has_handwriting'.
        """
        
        # 1. Text Density
        # Adaptive thresholding to binarize text vs background
        binary = cv2.adaptiveThreshold(
            image_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Count white pixels (which represent ink/text in the inverted binary image)
        ink_pixels = cv2.countNonZero(binary)
        total_pixels = image_gray.size
        text_density = ink_pixels / total_pixels
        
        # 2. Stamps Detection (Heuristic: Look for significant amounts of Blue or Red ink)
        # Convert to HSV color space
        hsv = cv2.cvtColor(image_color, cv2.COLOR_BGR2HSV)
        
        # Define ranges for Blue
        lower_blue = np.array([100, 50, 50])
        upper_blue = np.array([130, 255, 255])
        
        # Define ranges for Red
        lower_red1 = np.array([0, 50, 50])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 50, 50])
        upper_red2 = np.array([180, 255, 255])
        
        mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)
        
        mask_stamps = cv2.bitwise_or(mask_blue, mask_red)
        stamp_pixels = cv2.countNonZero(mask_stamps)
        
        # If more than 0.5% of the page is blue/red ink, we guess there is a stamp/signature
        has_stamps = bool(stamp_pixels > (total_pixels * 0.005))
        
        return {
            "text_density": float(text_density),
            "has_stamps": has_stamps,
            "has_signatures": has_stamps, # Stub for MVP: grouped with stamps logic
            "has_handwriting": False,     # Very hard to do reliably without ML, default false
        }
