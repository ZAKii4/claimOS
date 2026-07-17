from collections import defaultdict
from typing import Any

from app.engines.classification.base import BaseClassifier
from app.engines.classification.models import ClassificationPrediction, DocumentClass


class EnsembleClassifier:
    """
    Combines predictions from multiple BaseClassifiers using Weighted Majority Voting.
    """
    def __init__(self, classifiers: list[BaseClassifier]):
        self.classifiers = classifiers
        # Weights can be tuned based on model reliability
        self.weights = {
            "rules_classifier": 2.0,  # Rules are usually highly accurate when they hit
            "ocr_classifier": 1.0,
            "visual_classifier": 0.8
        }

    def predict_ensemble(self, features: dict[str, Any]) -> list[ClassificationPrediction]:
        # Aggregate scores
        aggregated_scores: dict[DocumentClass, float] = defaultdict(float)
        # Weight of classifiers that actually voted for *this* class — not the
        # fixed sum of every classifier's weight. Normalizing by the latter
        # means a class only one classifier ever has an opinion about (e.g. a
        # rule with no OCR/visual counterpart) gets punished as if the silent
        # classifiers had voted against it, when they simply don't apply —
        # a single confident rule match could never clear the confidence
        # threshold no matter how right it was.
        voted_weight: dict[DocumentClass, float] = defaultdict(float)
        explanations: dict[DocumentClass, list[str]] = defaultdict(list)
        engines: dict[DocumentClass, set[str]] = defaultdict(set)

        for classifier in self.classifiers:
            preds = classifier.predict(features)
            weight = self.weights.get(classifier.name, 1.0)

            for p in preds:
                # Soft voting: confidence * weight
                aggregated_scores[p.document_class] += p.confidence * weight
                voted_weight[p.document_class] += weight
                explanations[p.document_class].append(p.explanation or f"Predicted by {classifier.name}")
                engines[p.document_class].add(classifier.name)

        # Normalize scores (very simplified approach)
        final_predictions = []
        for doc_class, score in aggregated_scores.items():
            # Softmax or simple normalization could go here. We'll do a simple pseudo-probability.
            normalized_score = min(score / voted_weight[doc_class], 1.0)

            final_predictions.append(ClassificationPrediction(
                document_class=doc_class,
                confidence=normalized_score,
                explanation=" | ".join(explanations[doc_class]),
                engines_used=list(engines[doc_class])
            ))

        # Sort descending by confidence
        final_predictions.sort(key=lambda x: x.confidence, reverse=True)
        return final_predictions
