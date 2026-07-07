import re
from typing import List
from app.governance.models import PIIDetection


class PIIDetector:
    """Regex-based PII detection engine."""

    PATTERNS = {
        "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        "phone_fr": r'(?:\+33|0)\s*[1-9](?:[\s.-]*\d{2}){4}',
        "iban": r'[A-Z]{2}\d{2}[\s]?[\dA-Z]{4}[\s]?[\dA-Z]{4}[\s]?[\dA-Z]{4}[\s]?[\dA-Z]{0,4}',
        "credit_card": r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
        "plate_fr": r'[A-Z]{2}-\d{3}-[A-Z]{2}',
        "ssn_fr": r'[12]\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{3}\s?\d{3}\s?\d{2}',
        "policy_number": r'POL-\d{6,10}',
        "contract_number": r'CTR-\d{6,10}',
    }

    @classmethod
    def scan(cls, text: str) -> List[PIIDetection]:
        """Scan text for PII and return all detections."""
        detections: List[PIIDetection] = []

        for pii_type, pattern in cls.PATTERNS.items():
            for match in re.finditer(pattern, text):
                detections.append(PIIDetection(
                    pii_type=pii_type,
                    value=match.group(),
                    confidence=1.0,
                    start=match.start(),
                    end=match.end(),
                ))

        return detections

    @classmethod
    def contains_pii(cls, text: str) -> bool:
        return len(cls.scan(text)) > 0
