import time

from app.agents.base import AgentResult, BaseAgent
from app.agents.context import AgentContext
from app.agents.shared_memory import SharedMemory
from app.config.settings import get_settings
from app.llm.guardrails import GuardrailsEngine
from app.llm.manager import LLMManager
from app.llm.models import LLMRequest, Message

FRAUD_SYSTEM_PROMPT = (
    "You are a fraud detection analyst for an insurance claims platform. Assess "
    "whether the following OCR-extracted document text shows signs of tampering, "
    "forgery, or fraud (e.g. inconsistent amounts, altered dates, suspicious "
    "wording, mentions of image editing tools). "
    "Respond with ONLY a JSON object of the form: "
    '{"fraud_score": <float 0.0-1.0, 0=certainly legitimate, 1=certainly fraudulent>, '
    '"reasoning": "<one sentence justification>"}.'
)


class FraudAgent(BaseAgent):
    id = "fraud_agent"
    name = "Fraud Detection Agent"
    version = "1.0.0"
    capabilities = ["fraud_detection", "anomaly_detection"]

    def __init__(self, llm_manager: LLMManager | None = None) -> None:
        self.llm = llm_manager or LLMManager()

    async def plan(self, context: AgentContext, memory: SharedMemory) -> bool:
        # Run only if OCR is done
        return bool(context.ocr_results)

    async def execute(self, context: AgentContext, memory: SharedMemory) -> AgentResult:
        start_time = time.time()

        ocr_text = context.ocr_results.get("text", "")
        if not ocr_text.strip():
            return AgentResult(
                status="FAILED",
                confidence=0.0,
                execution_time_ms=int((time.time() - start_time) * 1000),
                artifacts={},
                messages=["No OCR text available; cannot assess fraud risk."],
            )

        request = LLMRequest(
            model=get_settings().OLLAMA_FRAUD_MODEL,
            messages=[
                Message(role="system", content=FRAUD_SYSTEM_PROMPT),
                Message(role="user", content=ocr_text),
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
        )

        response = await self.llm.generate(request)
        parsed = GuardrailsEngine.validate_json_output(response.choices[0].content)

        fraud_score = max(0.0, min(1.0, float(parsed.get("fraud_score", 0.5))))
        reasoning = str(parsed.get("reasoning", ""))
        is_fraud = fraud_score > 0.5
        # Confidence in the *verdict* (how far the score sits from the 0.5 midpoint).
        confidence = max(fraud_score, 1.0 - fraud_score)

        context.metadata["fraud_score"] = fraud_score

        memory.add_observation(
            self.id, {"fraud_suspected": is_fraud, "reasoning": reasoning}, confidence=confidence
        )

        execution_time = int((time.time() - start_time) * 1000)

        return AgentResult(
            status="SUCCESS",
            confidence=confidence,
            execution_time_ms=execution_time,
            artifacts={"fraud_score": fraud_score, "reasoning": reasoning},
            messages=[f"Fraud evaluation completed. Suspected: {is_fraud}. {reasoning}"],
        )

    async def validate(self, result: AgentResult) -> bool:
        return result.confidence > 0.0
