from pydantic import BaseModel
from typing import Dict, Any


class EvaluationScore(BaseModel):
    faithfulness: float
    grounding: float
    hallucination: float
    json_validity: float
    is_acceptable: bool


class EvaluationEngine:
    """Evaluates the quality of local LLM responses."""

    @classmethod
    def evaluate_response(cls, response: str, expected_context: str) -> EvaluationScore:
        """Simulates calculating NLP metrics for a response."""
        # Simple determinist simulation
        if "ERROR" in response.upper():
            return EvaluationScore(
                faithfulness=0.1, grounding=0.1, hallucination=0.9, json_validity=0.0, is_acceptable=False
            )
            
        # Standard valid response mock
        return EvaluationScore(
            faithfulness=0.95,
            grounding=0.98,
            hallucination=0.02,
            json_validity=1.0,
            is_acceptable=True
        )
