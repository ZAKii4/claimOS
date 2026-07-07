import re

class Validator:
    """
    Business rules to validate whether a normalized value is logically correct.
    """
    
    @staticmethod
    def is_valid_license_plate(plate: str) -> bool:
        """
        Basic validation for French SIV (AB123CD) or FNI (1234AB56) plates.
        """
        plate = plate.upper()
        siv_pattern = re.compile(r"^[A-Z]{2}\d{3}[A-Z]{2}$")
        fni_pattern = re.compile(r"^\d{1,4}[A-Z]{2,3}\d{2}$")
        return bool(siv_pattern.match(plate) or fni_pattern.match(plate))

    @staticmethod
    def is_valid_policy_number(policy: str) -> bool:
        """
        Basic length and character check for insurance policy numbers.
        Usually alphanumeric between 5 and 20 chars.
        """
        if not policy:
            return False
        cleaned = re.sub(r"[^A-Z0-9]", "", policy.upper())
        return 5 <= len(cleaned) <= 20
