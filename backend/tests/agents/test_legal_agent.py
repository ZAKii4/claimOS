import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

from app.agents.context import AgentContext
from app.agents.modules.legal_agent import LegalAgent
from app.agents.shared_memory import SharedMemory
from app.llm.models import CostMetrics, LLMResponse, Message, TokenUsage


def _entity(value, confidence=0.9, status="FOUND"):
    return {"value": value, "status": status, "confidence": confidence}


def _mock_llm_response(payload: dict) -> LLMResponse:
    return LLMResponse(
        id="test",
        provider_name="Ollama",
        model="qwen2.5",
        choices=[Message(role="assistant", content=json.dumps(payload))],
        usage=TokenUsage(),
        cost=CostMetrics(),
        latency_ms=1,
    )


def test_plan_requires_entities():
    agent = LegalAgent(llm_manager=MagicMock())
    memory = SharedMemory()
    assert asyncio.run(agent.plan(AgentContext(claim_id="C-1"), memory)) is False
    ctx = AgentContext(claim_id="C-1", entities={"numero_police": _entity("AXA123")})
    assert asyncio.run(agent.plan(ctx, memory)) is True


def test_deterministic_check_flags_policy_expired_before_accident():
    mock_manager = MagicMock()
    mock_manager.generate = AsyncMock(
        return_value=_mock_llm_response({"issues": [], "confidence": 0.9})
    )
    agent = LegalAgent(llm_manager=mock_manager)
    memory = SharedMemory()

    context = AgentContext(
        claim_id="C-1",
        entities={
            "date_effet_contrat": _entity("2020-01-01"),
            "date_echeance_contrat": _entity("2020-12-31"),
            "date_survenance": _entity("2026-07-10"),  # long after policy expired
        },
    )

    result = asyncio.run(agent.execute(context, memory))

    assert result.status == "SUCCESS"
    assert context.validation_report["compliant"] is False
    assert any("valide" in issue for issue in context.validation_report["issues"])


def test_deterministic_check_flags_licence_obtained_after_accident():
    mock_manager = MagicMock()
    mock_manager.generate = AsyncMock(
        return_value=_mock_llm_response({"issues": [], "confidence": 0.9})
    )
    agent = LegalAgent(llm_manager=mock_manager)
    memory = SharedMemory()

    context = AgentContext(
        claim_id="C-1",
        entities={
            "date_survenance": _entity("2026-01-01"),
            "conducteur.date_permis": _entity("2026-06-01"),  # permis obtained AFTER the accident
        },
    )

    result = asyncio.run(agent.execute(context, memory))

    assert result.status == "SUCCESS"
    assert context.validation_report["compliant"] is False
    assert any("permis" in issue for issue in context.validation_report["issues"])


def test_coherent_dossier_with_no_llm_issues_is_compliant():
    mock_manager = MagicMock()
    mock_manager.generate = AsyncMock(
        return_value=_mock_llm_response({"issues": [], "confidence": 0.95})
    )
    agent = LegalAgent(llm_manager=mock_manager)
    memory = SharedMemory()

    context = AgentContext(
        claim_id="C-1",
        entities={
            "date_effet_contrat": _entity("2025-01-01"),
            "date_echeance_contrat": _entity("2026-12-31"),
            "date_survenance": _entity("2026-06-01"),
            "conducteur.date_permis": _entity("2020-01-01"),
            "circonstances_accident": _entity("Choc arrière à un feu rouge."),
        },
    )

    result = asyncio.run(agent.execute(context, memory))

    assert result.status == "SUCCESS"
    assert context.validation_report["compliant"] is True
    assert context.validation_report["issues"] == []


def test_llm_failure_degrades_to_deterministic_findings_only():
    mock_manager = MagicMock()
    mock_manager.generate = AsyncMock(side_effect=RuntimeError("Ollama unreachable"))
    agent = LegalAgent(llm_manager=mock_manager)
    memory = SharedMemory()

    context = AgentContext(
        claim_id="C-1",
        entities={
            "date_effet_contrat": _entity("2020-01-01"),
            "date_echeance_contrat": _entity("2020-12-31"),
            "date_survenance": _entity("2026-07-10"),
            "circonstances_accident": _entity("Some free text so the LLM path is attempted."),
        },
    )

    result = asyncio.run(agent.execute(context, memory))

    # Deterministic finding survives even though the LLM call blew up.
    assert result.status == "SUCCESS"
    assert context.validation_report["compliant"] is False
    assert any("valide" in issue for issue in context.validation_report["issues"])
    assert context.validation_report["llm_enriched"] is False
