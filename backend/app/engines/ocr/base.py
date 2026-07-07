"""
Base abstract contract for all OCR Adapters.
"""

from abc import ABC, abstractmethod

import numpy as np

from app.engines.ocr.models import OCRPage


class BaseOCRAdapter(ABC):
    """
    Adapter interface forcing any OCR engine to produce the exact same standard output format.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the OCR engine."""
        pass
        
    @property
    @abstractmethod
    def version(self) -> str:
        """Version of the underlying library."""
        pass

    @abstractmethod
    def initialize(self) -> None:
        """Load ML models into memory."""
        pass

    @abstractmethod
    def process(self, image: np.ndarray) -> OCRPage:
        """
        Execute OCR on the given image array.
        Must return a standardized OCRPage.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Checks if the underlying ML library is installed and models are available.
        """
        pass
