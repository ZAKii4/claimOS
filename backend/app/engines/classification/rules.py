import re
from typing import Any

from app.engines.classification.base import BaseClassifier
from app.engines.classification.models import ClassificationPrediction, DocumentClass


class RulesClassifier(BaseClassifier):
    """
    Business rules classifier for deterministic document routing.
    Matches hardcoded patterns in features.
    """

    @property
    def name(self) -> str:
        return "rules_classifier"

    def predict(self, features: dict[str, Any]) -> list[ClassificationPrediction]:
        predictions = []
        raw_text = features.get("raw_text", "").lower()
        
        # Rule 1: Medical Certificate
        if "certificat médical" in raw_text or "itt" in raw_text:
            # Check layout features to increase confidence
            confidence = 0.7
            if features.get("num_signatures", 0) > 0 and features.get("num_stamps", 0) > 0:
                confidence = 0.95
                
            predictions.append(ClassificationPrediction(
                document_class=DocumentClass(family="Medical Certificate"),
                confidence=confidence,
                explanation="Matched keywords 'certificat médical' and found signatures/stamps",
                engines_used=[self.name]
            ))

        # Rule 2: Police Report
        if "constat amiable" in raw_text or "déclaration d'accident" in raw_text:
            predictions.append(ClassificationPrediction(
                document_class=DocumentClass(family="Police Report", subtype="Constat Amiable"),
                confidence=0.9,
                explanation="Matched keyword 'constat amiable'",
                engines_used=[self.name]
            ))

        # Rule 3: Identity Card
        if "carte nationale d'identité" in raw_text or "république française" in raw_text:
            # ID cards usually don't have tables but might have specific form fields
            predictions.append(ClassificationPrediction(
                document_class=DocumentClass(family="Identity Card"),
                confidence=0.85,
                explanation="Matched ID card keywords",
                engines_used=[self.name]
            ))
            
        # Sort predictions by confidence descending
        predictions.sort(key=lambda x: x.confidence, reverse=True)
        return predictions
