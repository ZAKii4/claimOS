from typing import Dict, Any

class DecisionCopilotEngine:
    """AI Assistant to explain decisions and recommend next actions."""

    @classmethod
    def chat(cls, claim_id: str, message: str) -> Dict[str, Any]:
        return {
            "claim_id": claim_id,
            "query": message,
            "response": f"Based on the analysis, this claim triggers 3 alerts. The OCR confidence was 98%. Recommendation: Request manual invoice review.",
            "sources": ["Invoice_OCR_Result.json", "FraudRule_44"]
        }
