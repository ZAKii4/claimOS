"""
Decision Agent.

Synthesizes what the upstream agents found (extraction completeness, fraud
score, legal compliance) into one recommendation, using the same DecisionType
vocabulary as the deterministic app/engines/decision/ engine so both systems
speak the same language — even though this agent reasons over a different,
higher-level input than that engine (which needs a full EvidenceGraphResult +
ValidationReport produced mid-pipeline; this agent works from the fused,
already-persisted claim data instead, see docs/COURS_05_ORCHESTRATION.md).

Safety property: a deterministic rule layer runs first and can only steer
towards *more* scrutiny (FRAUD_REVIEW, HUMAN_REVIEW, REQUEST_MORE_DOCUMENTS) —
it never auto-approves. Only when none of those triggers fire does the agent
ask the LLM for a nuanced recommendation, and even then AUTO_APPROVED requires
an explicit, confident LLM verdict — any failure or ambiguity defaults to
HUMAN_REVIEW, never to silently approving a claim.
"""

import time

from app.agents.base import AgentResult, BaseAgent
from app.agents.context import AgentContext
from app.agents.shared_memory import SharedMemory
from app.config.settings import get_settings
from app.engines.decision.models import DecisionType
from app.llm.guardrails import GuardrailsEngine
from app.llm.manager import LLMManager
from app.llm.models import LLMRequest, Message

DECISION_SYSTEM_PROMPT = (
    "Tu es le moteur de décision d'une plateforme de gestion de sinistres automobile. "
    "On te donne le taux de complétude des données extraites, le score de fraude, et les "
    "constats de conformité légale d'un dossier. Recommande une décision parmi: "
    '"AUTO_APPROVED", "HUMAN_REVIEW", "REQUEST_MORE_DOCUMENTS". '
    "Ne recommande AUTO_APPROVED que si tout est cohérent et complet. Réponds avec "
    'UNIQUEMENT un objet JSON: {"decision": "<une des 3 valeurs>", '
    '"reason": "<une phrase>", "confidence": <0.0-1.0>}.'
)

FRAUD_REVIEW_THRESHOLD = 0.7
MIN_COMPLETENESS_FOR_AUTO = 0.5


class DecisionAgent(BaseAgent):
    id = "decision_agent"
    name = "Decision Recommendation Agent"
    version = "1.0.0"
    capabilities = ["decision_support"]

    def __init__(self, llm_manager: LLMManager | None = None) -> None:
        self.llm = llm_manager or LLMManager()

    async def plan(self, context: AgentContext, memory: SharedMemory) -> bool:
        return bool(memory.get_observations_by_agent("fraud_agent")) and bool(
            context.validation_report
        )

    async def execute(self, context: AgentContext, memory: SharedMemory) -> AgentResult:
        start_time = time.time()

        fraud_score = float(context.metadata.get("fraud_score", 0.0))
        completeness = float(context.metadata.get("extraction_completeness", 0.0))
        legal_issues = context.validation_report.get("issues", [])

        decision, reason, confidence = self._deterministic_verdict(
            fraud_score, completeness, legal_issues
        )

        if decision is None:
            decision, reason, confidence = await self._llm_verdict(
                fraud_score, completeness, legal_issues
            )

        context.decision = {
            "decision": decision.value,
            "reason": reason,
            "confidence": confidence,
            "fraud_score": fraud_score,
            "completeness": completeness,
            "legal_issue_count": len(legal_issues),
        }

        memory.add_observation(self.id, context.decision, confidence=confidence)

        return AgentResult(
            status="SUCCESS",
            confidence=confidence,
            execution_time_ms=int((time.time() - start_time) * 1000),
            artifacts=context.decision,
            messages=[f"Decision: {decision.value} — {reason}"],
        )

    @staticmethod
    def _deterministic_verdict(
        fraud_score: float, completeness: float, legal_issues: list[str]
    ) -> tuple[DecisionType | None, str, float]:
        """Rules that can only escalate scrutiny — never approve. None means 'defer to LLM'."""
        if fraud_score > FRAUD_REVIEW_THRESHOLD:
            return (
                DecisionType.FRAUD_REVIEW,
                f"Score de fraude élevé ({fraud_score:.2f}) — révision fraude requise.",
                fraud_score,
            )
        if legal_issues:
            return (
                DecisionType.HUMAN_REVIEW,
                f"{len(legal_issues)} incohérence(s) légale(s) détectée(s) — "
                "révision humaine requise.",
                0.9,
            )
        if completeness < MIN_COMPLETENESS_FOR_AUTO:
            return (
                DecisionType.REQUEST_MORE_DOCUMENTS,
                f"Dossier incomplet ({completeness:.0%} des champs trouvés) — pièces "
                "complémentaires nécessaires.",
                1.0 - completeness,
            )
        return None, "", 0.0

    async def _llm_verdict(
        self, fraud_score: float, completeness: float, legal_issues: list[str]
    ) -> tuple[DecisionType, str, float]:
        summary = (
            f"Complétude des données extraites: {completeness:.0%}\n"
            f"Score de fraude: {fraud_score:.2f}\n"
            f"Incohérences légales: {len(legal_issues)}"
        )
        try:
            request = LLMRequest(
                model=get_settings().OLLAMA_DECISION_MODEL,
                messages=[
                    Message(role="system", content=DECISION_SYSTEM_PROMPT),
                    Message(role="user", content=summary),
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            response = await self.llm.generate(request)
            parsed = GuardrailsEngine.validate_json_output(response.choices[0].content)
            raw_decision = str(parsed.get("decision", "HUMAN_REVIEW"))
            decision = DecisionType(raw_decision) if raw_decision in DecisionType.__members__ else (
                DecisionType.HUMAN_REVIEW
            )
            reason = str(parsed.get("reason", "Recommandation du modèle."))
            confidence = max(0.0, min(1.0, float(parsed.get("confidence", 0.5))))
            return decision, reason, confidence
        except Exception as e:
            # Never silently approve when the reasoning step itself failed.
            return (
                DecisionType.HUMAN_REVIEW,
                f"Décision automatique indisponible ({e}) — révision humaine par défaut.",
                0.0,
            )

    async def validate(self, result: AgentResult) -> bool:
        return result.status == "SUCCESS"
