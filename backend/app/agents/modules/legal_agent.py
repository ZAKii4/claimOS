"""
Legal / Compliance Agent.

Checks a claim's fused opening form (via AgentContext.entities, populated by
ExtractionAgent) for legal and regulatory coherence: policy validity window,
driving licence validity, and judicial-procedure consistency.

Two layers, deliberately kept separate:
  1. Deterministic date-based rules (exact, no LLM, always run — insurance
     compliance checks like "was the policy active on the accident date"
     have a single correct answer and should never depend on an LLM call
     succeeding).
  2. An LLM pass over the free-text legal fields (circonstances, procédure
     judiciaire, avocat adverse, victim exclusions) to catch issues no fixed
     rule anticipates. This layer is best-effort: if the LLM call fails, the
     agent still returns the deterministic findings rather than failing
     outright — same degrade-not-fabricate policy as LLMFieldExtractor.
"""

import time
from datetime import date, datetime

from app.agents.base import AgentResult, BaseAgent
from app.agents.context import AgentContext
from app.agents.shared_memory import SharedMemory
from app.config.settings import get_settings
from app.llm.guardrails import GuardrailsEngine
from app.llm.manager import LLMManager
from app.llm.models import LLMRequest, Message

LEGAL_SYSTEM_PROMPT = (
    "Tu es un analyste conformité juridique pour une plateforme de gestion de sinistres "
    "automobile. On te donne un résumé texte des champs juridiquement pertinents d'un "
    "dossier (procédure judiciaire, juridiction, avocat adverse, exclusions de garantie "
    "des victimes, circonstances). Identifie toute incohérence ou point d'attention "
    "juridique que des règles fixes ne couvriraient pas. Réponds avec UNIQUEMENT un objet "
    'JSON de la forme : {"issues": ["<constat court>", ...], "confidence": <0.0-1.0>}. '
    "Liste vide si rien à signaler. N'invente rien qui ne soit pas dans le texte fourni."
)


def _parse_date(value: object) -> date | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.strip()).date()
    except ValueError:
        return None


def _field_value(entities: dict[str, dict], path: str) -> object:
    entry = entities.get(path)
    return entry.get("value") if entry else None


def _run_deterministic_checks(entities: dict[str, dict]) -> list[str]:
    issues: list[str] = []

    date_effet = _parse_date(_field_value(entities, "date_effet_contrat"))
    date_echeance = _parse_date(_field_value(entities, "date_echeance_contrat"))
    date_survenance = _parse_date(_field_value(entities, "date_survenance"))

    if date_effet and date_echeance and date_survenance:
        if date_survenance < date_effet or date_survenance > date_echeance:
            issues.append(
                f"La police (effet {date_effet.isoformat()} → échéance "
                f"{date_echeance.isoformat()}) n'était pas valide à la date du sinistre "
                f"({date_survenance.isoformat()})."
            )

    date_permis = _parse_date(_field_value(entities, "conducteur.date_permis"))
    if date_permis and date_survenance and date_permis > date_survenance:
        issues.append(
            f"Le permis de conduire du conducteur (obtenu le {date_permis.isoformat()}) est "
            f"postérieur à la date du sinistre ({date_survenance.isoformat()})."
        )

    procedure = _field_value(entities, "procedure_judiciaire")
    juridiction = _field_value(entities, "juridiction")
    if procedure and not juridiction:
        issues.append(
            "Une procédure judiciaire est mentionnée mais aucune juridiction n'est renseignée."
        )

    return issues


def _legal_text_summary(entities: dict[str, dict]) -> str:
    relevant_paths = [
        "circonstances_accident",
        "description",
        "procedure_judiciaire",
        "juridiction",
        "avocat_adverse",
        "cas_bareme",
        "responsabilite_pct",
    ]
    lines = [
        f"{path}: {_field_value(entities, path)}"
        for path in relevant_paths
        if _field_value(entities, path) not in (None, "")
    ]
    for path, entry in entities.items():
        if path.startswith("victimes.") and path.endswith(".exclue_garantie") and entry["value"]:
            lines.append(f"{path}: {entry['value']}")
    return "\n".join(lines)


class LegalAgent(BaseAgent):
    id = "legal_agent"
    name = "Legal Compliance Agent"
    version = "1.0.0"
    capabilities = ["legal_compliance", "regulatory_check"]

    def __init__(self, llm_manager: LLMManager | None = None) -> None:
        self.llm = llm_manager or LLMManager()

    async def plan(self, context: AgentContext, memory: SharedMemory) -> bool:
        return bool(context.entities)

    async def execute(self, context: AgentContext, memory: SharedMemory) -> AgentResult:
        start_time = time.time()

        issues = _run_deterministic_checks(context.entities)
        confidence = 0.6
        llm_ran = False

        text_summary = _legal_text_summary(context.entities)
        if text_summary.strip():
            try:
                request = LLMRequest(
                    model=get_settings().OLLAMA_LEGAL_MODEL,
                    messages=[
                        Message(role="system", content=LEGAL_SYSTEM_PROMPT),
                        Message(role="user", content=text_summary),
                    ],
                    temperature=0.0,
                    response_format={"type": "json_object"},
                )
                response = await self.llm.generate(request)
                parsed = GuardrailsEngine.validate_json_output(response.choices[0].content)
                issues.extend(str(i) for i in parsed.get("issues") or [])
                confidence = max(0.0, min(1.0, float(parsed.get("confidence", 0.9))))
                llm_ran = True
            except Exception as e:
                # Degrade to deterministic-only findings rather than failing
                # the whole agent — an unreachable LLM shouldn't hide date
                # coherence issues we already computed for free.
                issues.append(f"[analyse LLM indisponible: {e}]")

        is_compliant = len(issues) == 0 or (len(issues) == 1 and "LLM indisponible" in issues[0])
        context.validation_report = {
            "source": self.id,
            "compliant": is_compliant,
            "issues": [i for i in issues if not i.startswith("[analyse LLM indisponible")],
            "llm_enriched": llm_ran,
        }

        memory.add_observation(
            self.id,
            {"compliant": is_compliant, "issues": context.validation_report["issues"]},
            confidence=confidence,
        )

        execution_time = int((time.time() - start_time) * 1000)
        return AgentResult(
            status="SUCCESS",
            confidence=confidence,
            execution_time_ms=execution_time,
            artifacts=context.validation_report,
            messages=[
                f"Legal review completed: "
                f"{len(context.validation_report['issues'])} issue(s) found."
            ],
        )

    async def validate(self, result: AgentResult) -> bool:
        return result.status == "SUCCESS"
