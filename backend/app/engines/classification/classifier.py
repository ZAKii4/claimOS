from typing import Any

from app.engines.classification.base import BaseClassifier
from app.engines.classification.models import ClassificationPrediction, DocumentClass


class OCRClassifier(BaseClassifier):
    """
    Mock classifier using text features.
    In a real system, this would load a pre-trained scikit-learn model or embeddings.
    """
    @property
    def name(self) -> str:
        return "ocr_classifier"

    def predict(self, features: dict[str, Any]) -> list[ClassificationPrediction]:
        predictions = []
        raw_text = features.get("raw_text", "").lower()
        
        # Simple frequency heuristic to mock ML output
        if "facture" in raw_text or "tva" in raw_text:
            predictions.append(ClassificationPrediction(
                document_class=DocumentClass(family="Invoice"),
                confidence=0.6,
                explanation="High TF-IDF score for 'facture/tva'",
                engines_used=[self.name]
            ))
            
        return predictions


class VisualClassifier(BaseClassifier):
    """
    Mock classifier using visual/layout features.
    In a real system, this could be a ResNet or LayoutLM predicting document type.
    """
    @property
    def name(self) -> str:
        return "visual_classifier"

    def predict(self, features: dict[str, Any]) -> list[ClassificationPrediction]:
        predictions = []
        
        if features.get("num_tables", 0) > 1 and features.get("num_signatures", 0) == 0:
            # Lots of tables might indicate an Invoice or Repair Estimate
            predictions.append(ClassificationPrediction(
                document_class=DocumentClass(family="Repair Estimate"),
                confidence=0.5,
                explanation="Dense table layout detected",
                engines_used=[self.name]
            ))
            
        return predictions
