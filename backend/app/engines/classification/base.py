from abc import ABC, abstractmethod
from typing import Any, Optional

from app.engines.classification.models import ClassificationPrediction


class BaseClassifier(ABC):
    """
    Contract for an individual classification component (e.g. VisualClassifier, OCRClassifier, RulesClassifier).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name of the classifier."""
        ...

    @abstractmethod
    def predict(self, features: dict[str, Any]) -> list[ClassificationPrediction]:
        """
        Produce predictions based on the extracted features.
        
        Args:
            features: Dictionary containing extracted features (e.g., text, layout stats).
            
        Returns:
            A list of predictions sorted by confidence descending.
        """
        ...
