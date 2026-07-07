"""
Geometry operations: Deskew, Rotate, Resize.
"""

from typing import Any

import cv2
import numpy as np

from app.engines.preprocessing.operations.base import BaseOperation


class DeskewOperation(BaseOperation):
    
    def __init__(self, angle_degrees: float) -> None:
        self.angle_degrees = angle_degrees

    @property
    def name(self) -> str:
        return "deskew"

    def process(self, image: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
        # If angle is extremely small, skip to save time
        if abs(self.angle_degrees) < 0.1:
            return image, {"angle": self.angle_degrees, "skipped": True}
            
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        
        # Calculate rotation matrix
        M = cv2.getRotationMatrix2D(center, self.angle_degrees, 1.0)
        
        # We need to determine the new bounding box to avoid cutting off corners
        cos = np.abs(M[0, 0])
        sin = np.abs(M[0, 1])
        new_w = int((h * sin) + (w * cos))
        new_h = int((h * cos) + (w * sin))
        
        # Adjust the rotation matrix to take into account translation
        M[0, 2] += (new_w / 2) - center[0]
        M[1, 2] += (new_h / 2) - center[1]
        
        # Perform the actual rotation, padding with white (255)
        # If the image is color (3 channels), borderValue is (255, 255, 255)
        bg_color = (255, 255, 255) if len(image.shape) == 3 else 255
        
        deskewed = cv2.warpAffine(
            image, M, (new_w, new_h),
            flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=bg_color
        )
        
        return deskewed, {"angle": self.angle_degrees}


class RotateOperation(BaseOperation):
    
    def __init__(self, rotation_code: int) -> None:
        """
        rotation_code: 90, 180, 270 degrees.
        """
        self.rotation_code = rotation_code

    @property
    def name(self) -> str:
        return "rotate"

    def process(self, image: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
        if self.rotation_code == 90:
            rotated = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        elif self.rotation_code == 180:
            rotated = cv2.rotate(image, cv2.ROTATE_180)
        elif self.rotation_code == 270:
            rotated = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        else:
            rotated = image
            
        return rotated, {"rotation": self.rotation_code}
