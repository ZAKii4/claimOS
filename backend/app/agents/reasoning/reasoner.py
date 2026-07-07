from typing import Dict, Any, List
from pydantic import BaseModel, Field
import uuid
from enum import Enum
from app.agents.reasoning.policies import ExecutionPolicyManager


class ReasoningStrategy(str, Enum):
    DEDUCTIVE = "DEDUCTIVE"
    INDUCTIVE = "INDUCTIVE"
    ABDUCTIVE = "ABDUCTIVE"
    RULE_BASED = "RULE_BASED"
    GRAPH = "GRAPH"


class ReasoningResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    strategy: ReasoningStrategy
    conclusion: str
    confidence: float
    justification: List[str]
    is_blocked_by_policy: bool = False


class ReasoningEngine:
    """Produces explainable conclusions using various strategies."""

    @classmethod
    def reason(
        cls, 
        tenant_id: str, 
        context: Dict[str, Any], 
        strategy: ReasoningStrategy = ReasoningStrategy.RULE_BASED
    ) -> ReasoningResult:
        """Simulates autonomous reasoning."""
        
        result = ReasoningResult(
            tenant_id=tenant_id,
            strategy=strategy,
            conclusion="Indeterminate",
            confidence=0.0,
            justification=[]
        )

        # Policy check
        if ExecutionPolicyManager.requires_human_supervision(tenant_id):
            result.is_blocked_by_policy = True
            result.conclusion = "Action requires human supervision."
            result.justification.append(f"Tenant autonomy level is {ExecutionPolicyManager.get_level(tenant_id)}")
            return result

        # Mocking the reasoning logic based on context and strategy
        if strategy == ReasoningStrategy.DEDUCTIVE:
            if context.get("fraud_score", 0) > 80:
                result.conclusion = "Reject Claim"
                result.confidence = 0.95
                result.justification = ["Fraud score is above threshold (80).", "Deduction: High fraud implies rejection."]
            else:
                result.conclusion = "Approve Claim"
                result.confidence = 0.85
                result.justification = ["Fraud score is low.", "All documents are present."]
        elif strategy == ReasoningStrategy.GRAPH:
            result.conclusion = "Identify Network"
            result.confidence = 0.90
            result.justification = ["Graph traversal found a cycle of 3 claims sharing the same IBAN."]
        else:
            result.conclusion = "Proceed normally"
            result.confidence = 0.75
            result.justification = ["Default rule-based evaluation."]

        return result
