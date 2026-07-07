"""
Base contract for all preprocessing operations.
"""

import time
from abc import ABC, abstractmethod
from typing import Any

import numpy as np

from app.engines.preprocessing.models import OperationRecord


class BaseOperation(ABC):
    """
    Abstract base class for a single image preprocessing transformation.
    Follows the Command pattern.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for the operation (e.g., 'DeskewOperation')."""
        pass

    @abstractmethod
    def process(self, image: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
        """
        Execute the specific image transformation.
        
        Args:
            image: The input image matrix (BGR or Grayscale).
            
        Returns:
            A tuple of (processed_image, parameters_used_dict).
        """
        pass

    def execute(self, image: np.ndarray) -> tuple[np.ndarray, OperationRecord]:
        """
        Wrapper to measure execution time and return standard OperationRecord.
        """
        start_time = time.perf_counter()
        
        processed_img, params = self.process(image)
        
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        
        record = OperationRecord(
            operation_name=self.name,
            execution_time_ms=elapsed_ms,
            parameters_used=params
        )
        
        return processed_img, record
