from typing import Dict, Any

class InvestigationWorkspace:
    """Centralizes claim information into a single interactive workspace."""

    @classmethod
    def get_workspace(cls, claim_id: str) -> Dict[str, Any]:
        return {
            "claim_id": claim_id,
            "timeline": ["Claim Created", "OCR Processed", "Agent Review"],
            "xai_explanation": "Approved due to high OCR confidence",
            "active_rules": ["RULE_001_FRAUD_CHECK"],
            "status": "READY_FOR_HUMAN"
        }
