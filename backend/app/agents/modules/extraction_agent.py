"""
Extraction Agent.

Unlike the other new agents (Legal, Decision), this one makes no LLM call —
its job is deterministic aggregation, not reasoning. The real field-level
extraction (regex + LLMFieldExtractor, 6 extractors) already runs inside the
linear document pipeline (app/pipeline/steps/extraction.py) and its fused
result is handed to this agent as a ClaimOpeningForm dict on
AgentContext.metadata["raw"]["opening_form"] (built by whoever calls
AgentManager.process_claim() — see app/api/v1/endpoints/agents.py).

This agent's role in the 6-agent collaboration is to flatten that fused form
into AgentContext.entities: a single, uniform view every downstream agent
(Legal, Decision, Supervisor) can read without knowing anything about
ClaimOpeningForm's nested Pydantic schema.
"""

import time

from app.agents.base import AgentResult, BaseAgent
from app.agents.context import AgentContext
from app.agents.shared_memory import SharedMemory
from app.engines.form_mapping.schema import ClaimOpeningForm, FieldStatus


def _flatten_form(form: ClaimOpeningForm) -> dict[str, dict]:
    """
    Walks every MappedField on a ClaimOpeningForm (including the nested
    ConducteurForm/PartieAdverseForm, and the victimes list) into a flat
    {dotted_path: {"value", "status", "confidence"}} dict.
    """
    entities: dict[str, dict] = {}

    def _walk(obj, prefix: str) -> None:
        if hasattr(obj, "status") and hasattr(obj, "value"):
            entities[prefix] = {
                "value": obj.value,
                "status": obj.status.value if hasattr(obj.status, "value") else obj.status,
                "confidence": obj.confidence,
            }
            return
        if hasattr(type(obj), "model_fields"):
            for field_name in type(obj).model_fields:
                child = getattr(obj, field_name)
                path = f"{prefix}.{field_name}" if prefix else field_name
                _walk(child, path)

    for field_name in ClaimOpeningForm.model_fields:
        if field_name == "victimes":
            continue
        _walk(getattr(form, field_name), field_name)

    for index, victime in enumerate(form.victimes):
        _walk(victime, f"victimes.{index}")

    return entities


class ExtractionAgent(BaseAgent):
    id = "extraction_agent"
    name = "Extraction Aggregation Agent"
    version = "1.0.0"
    capabilities = ["extraction_aggregation"]

    async def plan(self, context: AgentContext, memory: SharedMemory) -> bool:
        opening_form = context.metadata.get("raw", {}).get("opening_form")
        return bool(opening_form) and not context.entities

    async def execute(self, context: AgentContext, memory: SharedMemory) -> AgentResult:
        start_time = time.time()

        opening_form_data = context.metadata.get("raw", {}).get("opening_form")
        if not opening_form_data:
            return AgentResult(
                status="FAILED",
                confidence=0.0,
                execution_time_ms=int((time.time() - start_time) * 1000),
                artifacts={},
                messages=["No opening_form supplied in claim raw data; nothing to aggregate."],
            )

        form = ClaimOpeningForm(**opening_form_data)
        entities = _flatten_form(form)
        context.entities = entities

        found = [e for e in entities.values() if e["status"] == FieldStatus.FOUND.value]
        completeness = len(found) / len(entities) if entities else 0.0
        avg_confidence = sum(e["confidence"] for e in found) / len(found) if found else 0.0

        context.metadata["extraction_completeness"] = completeness

        memory.add_observation(
            self.id,
            {
                "fields_found": len(found),
                "fields_total": len(entities),
                "completeness": completeness,
            },
            confidence=avg_confidence,
        )

        return AgentResult(
            status="SUCCESS",
            confidence=avg_confidence,
            execution_time_ms=int((time.time() - start_time) * 1000),
            artifacts={
                "fields_found": len(found),
                "fields_total": len(entities),
                "completeness": completeness,
            },
            messages=[
                f"Aggregated {len(found)}/{len(entities)} fields from the fused opening form "
                f"({completeness:.0%} complete)."
            ],
        )

    async def validate(self, result: AgentResult) -> bool:
        return result.status == "SUCCESS"
