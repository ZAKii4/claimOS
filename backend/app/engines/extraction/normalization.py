import re
from typing import Any

class Normalizer:
    """
    Utility class to standardize extracted strings into consistent formats.
    """
    
    @staticmethod
    def normalize_license_plate(raw_plate: str) -> str:
        """
        Removes spaces, hyphens and normalizes to uppercase.
        e.g. 'AB-123-CD' -> 'AB123CD'
        """
        if not raw_plate:
            return ""
        return re.sub(r"[^A-Z0-9]", "", raw_plate.upper())

    @staticmethod
    def normalize_amount(raw_amount: str) -> float:
        """
        Converts European currency formats to float.
        e.g. '1 234,56 €' -> 1234.56
        """
        if not raw_amount:
            return 0.0
        cleaned = re.sub(r"[^\d,\.]", "", raw_amount)
        if "," in cleaned and "." in cleaned:
            # likely 1,234.56
            cleaned = cleaned.replace(",", "")
        else:
            # likely 1234,56
            cleaned = cleaned.replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    @staticmethod
    def normalize_text(raw_text: str) -> str:
        if not raw_text:
            return ""
        return " ".join(raw_text.strip().split())
