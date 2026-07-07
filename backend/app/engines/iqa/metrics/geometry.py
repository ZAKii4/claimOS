"""
Geometry and Alignment analysis (Deskew, Rotation).
"""

import math

import cv2
import numpy as np


class GeometryAnalyzer:
    
    def analyze(self, image_gray: np.ndarray) -> dict[str, float | int]:
        """
        Estimates the deskew angle of the document.
        Uses Canny Edge Detection and Hough Line Transform to find dominant text lines.
        
        Args:
            image_gray: Grayscale OpenCV image matrix.
            
        Returns:
            Dictionary with 'deskew_angle'.
        """
        # Edge detection
        edges = cv2.Canny(image_gray, 50, 150, apertureSize=3)
        
        # Probabilistic Hough Line Transform
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=100, maxLineGap=10)
        
        angle = 0.0
        if lines is not None:
            angles = []
            for line in lines:
                x1, y1, x2, y2 = line.flatten()[:4]
                # Calculate angle in degrees
                a = math.degrees(math.atan2(y2 - y1, x2 - x1))
                
                # We only care about lines that are roughly horizontal (typical text lines)
                if -45.0 <= a <= 45.0:
                    angles.append(a)
                    
            if angles:
                # Median angle of the horizontal-ish lines is our deskew estimate
                angle = np.median(angles)
                
        return {
            "deskew_angle": float(angle),
            "rotation": 0  # To detect 90/180/270, one would typically use OCR metadata (e.g. tesseract orientation)
        }
