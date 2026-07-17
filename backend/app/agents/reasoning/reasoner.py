import json
import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.agents.reasoning.policies import ExecutionPolicyManager
from app.config.settings import get_settings
from app.llm.guardrails import GuardrailsEngine
from app.llm.manager import LLMManager
from app.llm.models import LLMRequest, Message


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
    justification: list[str]
    is_blocked_by_policy: bool = False


REASONING_SYSTEM_PROMPT = (
    "You are the autonomous reasoning engine of an insurance claims AI platform, "
    "applying a {strategy} reasoning strategy. Given the JSON claim context below, "
    "produce a conclusion (a short recommended action, e.g. 'Approve Claim', "
    "'Reject Claim', 'Escalate for Review', 'Proceed normally'), a confidence "
    "score, and a justification. If the context includes a 'fraud_score', it is "
    "on a 0-100 scale where higher values indicate higher fraud risk (e.g. 10 is "
    "low risk, 90 is high risk) — it is NOT a 0-10 scale. Respond with ONLY a "
    "JSON object of the form: "
    '{{"conclusion": "<short action>", "confidence": <float 0.0-1.0>, '
    '"justification": ["<reasoning step>", ...]}}.'
)


class ReasoningEngine:
    """Produces explainable conclusions from claim context using a real LLM call."""

    @classmethod
    async def reason(
        cls,
        tenant_id: str,
        context: dict[str, Any],
        strategy: ReasoningStrategy = ReasoningStrategy.RULE_BASED,
        llm_manager: LLMManager | None = None,
    ) -> ReasoningResult:
        result = ReasoningResult(
            tenant_id=tenant_id,
            strategy=strategy,
            conclusion="Indeterminate",
            confidence=0.0,
            justification=[]
        )

        # Policy check (deterministic, no LLM needed)
        if ExecutionPolicyManager.requires_human_supervision(tenant_id):
            result.is_blocked_by_policy = True
            result.conclusion = "Action requires human supervision."
            autonomy_level = ExecutionPolicyManager.get_level(tenant_id)
            result.justification.append(f"Tenant autonomy level is {autonomy_level}")
            return result

        llm = llm_manager or LLMManager()
        request = LLMRequest(
            model=get_settings().OLLAMA_DEFAULT_MODEL,
            messages=[
                Message(
                    role="system",
                    content=REASONING_SYSTEM_PROMPT.format(strategy=strategy.value),
                ),
                Message(role="user", content=json.dumps(context)),
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        response = await llm.generate(request)
        parsed = GuardrailsEngine.validate_json_output(response.choices[0].content)

        result.conclusion = str(parsed.get("conclusion") or "Indeterminate")
        result.confidence = max(0.0, min(1.0, float(parsed.get("confidence", 0.0))))
        result.justification = [str(j) for j in (parsed.get("justification") or [])]

        return result
