from typing import Dict, Any, List

class RecommendationEngine:
    """Proactively suggests investigations and actions."""

    @classmethod
    def get_recommendations(cls, claim_id: str) -> List[Dict[str, Any]]:
        return [
            {"action": "REQUEST_DOCUMENT", "target": "Police Report", "roi": "HIGH", "confidence": 0.89},
            {"action": "CONSULT_EXPERT", "target": "Legal Advisor", "roi": "MEDIUM", "confidence": 0.72}
        ]
