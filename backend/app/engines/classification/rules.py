import re
import unicodedata
from typing import Any

from app.engines.classification.base import BaseClassifier
from app.engines.classification.models import ClassificationPrediction, DocumentClass


def _fold_accents(text: str) -> str:
    """
    Strips accents (é -> e, û -> u, ...) so keyword matching survives OCR
    engines that render them inconsistently — Tesseract drops accents on some
    all-caps headers, PaddleOCR on others, and never the same ones. Matching
    against a folded raw_text and unaccented keyword patterns avoids having to
    hand-enumerate every accented/unaccented spelling per keyword.
    """
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )


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
        raw_text = _fold_accents(features.get("raw_text", "").lower())

        # Rule 1: Medical Certificate
        # Accent-folded, and accepts OCR word-gluing ("CERTIFICAT MEDICAL"
        # reads back as "certificat medical" or, glued, "certificatmedical").
        # "itt" needs a word boundary — a bare substring check false-positives
        # on ordinary French words like "quITTance" (payment receipt).
        is_medical_certificate = (
            "certificat medical" in raw_text
            or "certificatmedical" in raw_text
            or re.search(r"\bi\.?t\.?t\.?\b", raw_text) is not None
        )
        if is_medical_certificate:
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

        # Rule 2: Police Report (French "constat amiable", or Moroccan police/gendarmerie PV)
        is_constat = "constat amiable" in raw_text or "declaration d'accident" in raw_text
        # OCR frequently glues adjacent words ("service des" -> "servicedes."), so the PV
        # signal is two independent, individually well-recognized keywords rather than one
        # long exact phrase: an issuing authority + an accident/circulation reference.
        has_authority = any(
            kw in raw_text for kw in ("prefecture", "gendarmerie royale", "surete nationale")
        )
        has_accident_ref = any(
            kw in raw_text for kw in ("accident", "circulation", "proces-verbal", "procesverbal")
        )
        is_moroccan_pv = has_authority and has_accident_ref

        if is_constat or is_moroccan_pv:
            predictions.append(ClassificationPrediction(
                document_class=DocumentClass(
                    family="Police Report",
                    subtype="Constat Amiable" if is_constat else "PV Police (Maroc)",
                ),
                confidence=0.9 if is_constat else 0.85,
                explanation=(
                    "Matched keyword 'constat amiable'" if is_constat
                    else "Matched Moroccan police PV keywords (authority + accident/circulation reference)"
                ),
                engines_used=[self.name]
            ))

        # Rule 3.5: Insurance Attestation
        # Two independent keyword hits rather than one exact phrase, for the same
        # OCR word-gluing reason as the Moroccan PV rule above.
        is_attestation = "attestation" in raw_text and "assurance" in raw_text
        if is_attestation:
            predictions.append(ClassificationPrediction(
                document_class=DocumentClass(family="Insurance Attestation"),
                confidence=0.85,
                explanation="Matched keywords 'attestation' and 'assurance'",
                engines_used=[self.name]
            ))

        # Rule 3: Identity Card
        if "carte nationale d'identite" in raw_text or "republique francaise" in raw_text:
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
