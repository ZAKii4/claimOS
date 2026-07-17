from typing import Dict, Any, List

class SituationAwarenessEngine:
    """Aggregates global platform alerts and categorizes them by criticality."""

    @classmethod
    def get_situation(cls) -> List[Dict[str, Any]]:
        return [
            {"type": "GPU_SATURATION", "cluster": "eu-central", "level": "HIGH", "message": "VRAM at 98%"},
            {"type": "FRAUD_ALERT", "cluster": "eu-west", "level": "CRITICAL", "message": "Syndicate detected"},
            {"type": "SLA_BREACH", "cluster": "af-north", "level": "MEDIUM", "message": "OCR delayed by 400ms"}
        ]
