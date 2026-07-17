import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

from app.agents.context import AgentContext
from app.agents.modules.decision_agent import DecisionAgent
from app.agents.shared_memory import SharedMemory
from app.engines.decision.models import DecisionType
from app.llm.models import CostMetrics, LLMResponse, Message, TokenUsage


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


def test_plan_requires_validation_report():
    agent = DecisionAgent(llm_manager=MagicMock())
    memory = SharedMemory()

    assert asyncio.run(agent.plan(AgentContext(claim_id="C-1"), memory)) is False

    ctx = AgentContext(claim_id="C-1", validation_report={"compliant": True, "issues": []})
    assert asyncio.run(agent.plan(ctx, memory)) is True


def test_plan_does_not_require_fraud_agent_to_have_run():
    """
    Regression test: fraud_agent legitimately skips when there's no OCR text
    (e.g. an empty claim) — decision_agent must still run in that case, since
    its own REQUEST_MORE_DOCUMENTS rule is exactly what handles it.
    """
    agent = DecisionAgent(llm_manager=MagicMock())
    memory = SharedMemory()  # no fraud_agent observation added at all

    ctx = AgentContext(claim_id="C-1", validation_report={"compliant": True, "issues": []})
    assert asyncio.run(agent.plan(ctx, memory)) is True


def test_high_fraud_score_forces_fraud_review_without_calling_llm():
    mock_manager = MagicMock()
    mock_manager.generate = AsyncMock()
    agent = DecisionAgent(llm_manager=mock_manager)
    memory = SharedMemory()
    memory.add_observation("fraud_agent", {}, confidence=0.9)

    context = AgentContext(
        claim_id="C-1",
        metadata={"fraud_score": 0.85, "extraction_completeness": 1.0},
        validation_report={"compliant": True, "issues": []},
    )

    result = asyncio.run(agent.execute(context, memory))

    assert context.decision["decision"] == DecisionType.FRAUD_REVIEW.value
    assert result.status == "SUCCESS"
    mock_manager.generate.assert_not_called()  # deterministic rule short-circuits the LLM call


def test_legal_issues_force_human_review():
    mock_manager = MagicMock()
    mock_manager.generate = AsyncMock()
    agent = DecisionAgent(llm_manager=mock_manager)
    memory = SharedMemory()
    memory.add_observation("fraud_agent", {}, confidence=0.9)

    context = AgentContext(
        claim_id="C-1",
        metadata={"fraud_score": 0.1, "extraction_completeness": 1.0},
        validation_report={"compliant": False, "issues": ["permis invalide"]},
    )

    result = asyncio.run(agent.execute(context, memory))

    assert context.decision["decision"] == DecisionType.HUMAN_REVIEW.value
    assert result.status == "SUCCESS"
    mock_manager.generate.assert_not_called()


def test_low_completeness_requests_more_documents():
    mock_manager = MagicMock()
    mock_manager.generate = AsyncMock()
    agent = DecisionAgent(llm_manager=mock_manager)
    memory = SharedMemory()
    memory.add_observation("fraud_agent", {}, confidence=0.9)

    context = AgentContext(
        claim_id="C-1",
        metadata={"fraud_score": 0.1, "extraction_completeness": 0.2},
        validation_report={"compliant": True, "issues": []},
    )

    result = asyncio.run(agent.execute(context, memory))

    assert context.decision["decision"] == DecisionType.REQUEST_MORE_DOCUMENTS.value
    assert result.status == "SUCCESS"


def test_clean_dossier_defers_to_llm_recommendation():
    mock_manager = MagicMock()
    mock_manager.generate = AsyncMock(
        return_value=_mock_llm_response(
            {
                "decision": "AUTO_APPROVED",
                "reason": "Dossier complet et cohérent.",
                "confidence": 0.95,
            }
        )
    )
    agent = DecisionAgent(llm_manager=mock_manager)
    memory = SharedMemory()
    memory.add_observation("fraud_agent", {}, confidence=0.9)

    context = AgentContext(
        claim_id="C-1",
        metadata={"fraud_score": 0.05, "extraction_completeness": 0.95},
        validation_report={"compliant": True, "issues": []},
    )

    result = asyncio.run(agent.execute(context, memory))

    assert context.decision["decision"] == DecisionType.AUTO_APPROVED.value
    assert result.confidence == 0.95
    mock_manager.generate.assert_called_once()


def test_llm_failure_never_silently_auto_approves():
    mock_manager = MagicMock()
    mock_manager.generate = AsyncMock(side_effect=RuntimeError("Ollama unreachable"))
    agent = DecisionAgent(llm_manager=mock_manager)
    memory = SharedMemory()
    memory.add_observation("fraud_agent", {}, confidence=0.9)

    context = AgentContext(
        claim_id="C-1",
        metadata={"fraud_score": 0.05, "extraction_completeness": 0.95},
        validation_report={"compliant": True, "issues": []},
    )

    result = asyncio.run(agent.execute(context, memory))

    assert result.status == "SUCCESS"
    assert context.decision["decision"] == DecisionType.HUMAN_REVIEW.value
    assert context.decision["confidence"] == 0.0
