from app.engines.classification.models import ClassificationPrediction, DocumentClass


class ConfidenceEngine:
    """
    Evaluates final predictions, calculates margin of confidence, and handles the UNKNOWN fallback.
    """
    
    def __init__(self, unknown_threshold: float = 0.4):
        self.unknown_threshold = unknown_threshold

    def evaluate(self, predictions: list[ClassificationPrediction]) -> list[ClassificationPrediction]:
        """
        Takes raw ensemble predictions and ensures they are reliable.
        Returns the top predictions. If top prediction < threshold, returns UNKNOWN.
        """
        if not predictions:
            return [self._get_unknown()]

        top_pred = predictions[0]

        if top_pred.confidence < self.unknown_threshold:
            # Fallback to UNKNOWN
            return [self._get_unknown(original_top=top_pred)]
            
        return predictions

    def _get_unknown(self, original_top: ClassificationPrediction | None = None) -> ClassificationPrediction:
        explanation = "Confidence below threshold."
        if original_top:
            explanation += f" Best guess was '{original_top.document_class.family}' at {original_top.confidence:.2f}."
            
        return ClassificationPrediction(
            document_class=DocumentClass(family="UNKNOWN_DOCUMENT"),
            confidence=1.0,
            explanation=explanation,
            engines_used=["confidence_engine"]
        )
