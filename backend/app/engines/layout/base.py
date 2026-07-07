from abc import ABC, abstractmethod
from typing import Any, Optional

import numpy as np

from app.engines.layout.models import LayoutRegion
from app.engines.ocr.models import OCRPage


class BaseDetector(ABC):
    """
    Base contract for all layout detectors.
    A detector is responsible for finding a specific type of region
    (e.g., tables, forms, signatures) using computer vision, rules, or ML.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for the detector."""
        ...

    @abstractmethod
    def detect(self, image: np.ndarray, ocr_page: Optional[OCRPage] = None) -> list[LayoutRegion]:
        """
        Run detection on a single page.
        
        Args:
            image: The original or preprocessed numpy image (BGR or Grayscale).
            ocr_page: Optional OCR results for the page, as some detectors 
                      (like FormDetector) rely on text and spatial arrangements.
                      
        Returns:
            A list of detected LayoutRegion objects.
        """
        ...
