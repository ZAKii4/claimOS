import asyncio

from app.agents.context import AgentContext
from app.agents.modules.extraction_agent import ExtractionAgent
from app.agents.shared_memory import SharedMemory
from app.engines.form_mapping.schema import ClaimOpeningForm, FieldStatus, MappedField


def _form_with_some_found_fields() -> dict:
    form = ClaimOpeningForm()
    form.numero_police = MappedField(value="AXA123", status=FieldStatus.FOUND, confidence=0.9)
    form.lieu_survenance = MappedField(
        value="Casablanca", status=FieldStatus.FOUND, confidence=0.8
    )
    form.conducteur.nom = MappedField(value="Dupont", status=FieldStatus.FOUND, confidence=0.7)
    return form.model_dump(mode="json")


def test_plan_runs_only_when_opening_form_present_and_entities_empty():
    agent = ExtractionAgent()
    memory = SharedMemory()

    empty_context = AgentContext(claim_id="C-1")
    assert asyncio.run(agent.plan(empty_context, memory)) is False

    context_with_form = AgentContext(
        claim_id="C-1", metadata={"raw": {"opening_form": _form_with_some_found_fields()}}
    )
    assert asyncio.run(agent.plan(context_with_form, memory)) is True


def test_execute_flattens_form_into_entities():
    agent = ExtractionAgent()
    memory = SharedMemory()
    context = AgentContext(
        claim_id="C-1", metadata={"raw": {"opening_form": _form_with_some_found_fields()}}
    )

    result = asyncio.run(agent.execute(context, memory))

    assert result.status == "SUCCESS"
    assert context.entities["numero_police"]["value"] == "AXA123"
    assert context.entities["numero_police"]["status"] == "FOUND"
    assert context.entities["conducteur.nom"]["value"] == "Dupont"
    # A field nobody filled in stays present but NOT_FOUND, never silently dropped.
    assert context.entities["date_survenance"]["status"] == "NOT_FOUND"
    assert 0.0 < context.metadata["extraction_completeness"] < 1.0


def test_execute_without_opening_form_fails_explicitly():
    agent = ExtractionAgent()
    memory = SharedMemory()
    context = AgentContext(claim_id="C-1")

    result = asyncio.run(agent.execute(context, memory))

    assert result.status == "FAILED"
    assert context.entities == {}
