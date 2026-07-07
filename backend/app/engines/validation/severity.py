from enum import IntEnum

class ValidationSeverity(IntEnum):
    """
    Severity levels for validation rules. 
    IntEnum allows for easy comparison (e.g., severity >= ValidationSeverity.ERROR).
    """
    INFO = 10
    WARNING = 20
    ERROR = 30
    CRITICAL = 40
    BLOCKER = 50
