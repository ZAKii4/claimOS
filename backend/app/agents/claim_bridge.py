"""
Bridges a claim's already-fused ``ClaimOpeningForm`` (produced by the linear
document pipeline + ``FormMappingEngine``, see ``DocumentService.get_opening_form``)
into the flat ``raw_data`` shape ``AgentManager.process_claim()`` expects on
``AgentContext.metadata["raw"]``.

Why this exists: no raw OCR text is persisted anywhere per document (only the
already-structured ``ExtractionResult`` is) — see docs/COURS_05_ORCHESTRATION.md
for why re-deriving it wasn't the right call. Agents that reason over free text
(FraudAgent, LegalAgent's LLM layer) instead read a compact, human-readable
summary built from every FOUND field of the fused form — real, non-fabricated
signal, just already structured rather than raw OCR output.
"""

from app.engines.form_mapping.schema import ClaimOpeningForm, FieldStatus


def _collect_found_lines(form: ClaimOpeningForm) -> tuple[list[str], list[float]]:
    lines: list[str] = []
    confidences: list[float] = []

    def _walk(obj, label: str) -> None:
        if hasattr(obj, "status") and hasattr(obj, "value"):
            if obj.status == FieldStatus.FOUND and obj.value not in (None, ""):
                lines.append(f"{label}: {obj.value}")
                confidences.append(obj.confidence)
            return
        if hasattr(type(obj), "model_fields"):
            for field_name in type(obj).model_fields:
                child = getattr(obj, field_name)
                _walk(child, f"{label}.{field_name}" if label else field_name)

    for field_name in ClaimOpeningForm.model_fields:
        if field_name == "victimes":
            continue
        _walk(getattr(form, field_name), field_name)

    for index, victime in enumerate(form.victimes):
        _walk(victime, f"victimes.{index}")

    return lines, confidences


def build_agent_raw_data(form: ClaimOpeningForm) -> dict:
    """
    Builds the ``raw_data`` payload for ``AgentManager.process_claim()``:
    - ``opening_form``: the full fused form, for ``ExtractionAgent`` to flatten.
    - ``ocr_text``: a text summary of every FOUND field, for agents that
      reason over free text (``FraudAgent``, ``LegalAgent``'s LLM layer),
      adopted as-is by ``OCRSupervisorAgent`` instead of triggering a real
      (and redundant) OCR run.
    - ``ocr_confidence``: average confidence across the summarized fields,
      0.0 if none were found (an empty dossier is not a confident one).
    """
    lines, confidences = _collect_found_lines(form)
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    return {
        "opening_form": form.model_dump(mode="json"),
        "ocr_text": "\n".join(lines),
        "ocr_confidence": avg_confidence,
    }
