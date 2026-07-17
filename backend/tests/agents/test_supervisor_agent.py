import asyncio

from app.agents.context import AgentContext
from app.agents.modules.supervisor_agent import SupervisorAgent
from app.agents.shared_memory import SharedMemory
from app.engines.decision.models import DecisionType


def test_plan_requires_a_decision():
    agent = SupervisorAgent()
    memory = SharedMemory()
    assert asyncio.run(agent.plan(AgentContext(claim_id="C-1"), memory)) is False
    ctx = AgentContext(claim_id="C-1", decision={"decision": "AUTO_APPROVED", "confidence": 0.9})
    assert asyncio.run(agent.plan(ctx, memory)) is True


def test_confident_decision_passes_through_unchanged():
    agent = SupervisorAgent()
    memory = SharedMemory()
    # Every upstream agent ran successfully — nothing should trigger an override.
    for agent_id in ("ocr_supervisor", "extraction_agent", "fraud_agent", "legal_agent"):
        memory.add_observation(agent_id, {}, confidence=1.0)
    memory.add_observation("decision_agent", {"decision": "AUTO_APPROVED"}, confidence=0.9)

    context = AgentContext(
        claim_id="C-1",
        decision={"decision": DecisionType.AUTO_APPROVED.value, "confidence": 0.9},
    )

    result = asyncio.run(agent.execute(context, memory))

    summary = context.metadata["supervisor_summary"]
    assert summary["final_decision"] == DecisionType.AUTO_APPROVED.value
    assert summary["overridden"] is False
    assert result.status == "SUCCESS"


def test_low_confidence_decision_is_overridden_to_human_review():
    agent = SupervisorAgent()
    memory = SharedMemory()
    memory.add_observation("decision_agent", {"decision": "AUTO_APPROVED"}, confidence=0.2)

    context = AgentContext(
        claim_id="C-1",
        decision={"decision": DecisionType.AUTO_APPROVED.value, "confidence": 0.2},
    )

    result = asyncio.run(agent.execute(context, memory))

    summary = context.metadata["supervisor_summary"]
    assert summary["final_decision"] == DecisionType.HUMAN_REVIEW.value
    assert summary["overridden"] is True
    assert result.status == "SUCCESS"


def test_failed_upstream_agent_forces_human_review_override():
    agent = SupervisorAgent()
    memory = SharedMemory()
    # decision_agent ran, but fraud_agent never produced an observation
    # (e.g. it failed or was skipped) — the supervisor should not let a
    # confident decision through without every upstream agent having run.
    memory.add_observation("decision_agent", {"decision": "AUTO_APPROVED"}, confidence=0.95)
    memory.add_observation("extraction_agent", {}, confidence=1.0)
    memory.add_observation("legal_agent", {}, confidence=1.0)

    context = AgentContext(
        claim_id="C-1",
        decision={"decision": DecisionType.AUTO_APPROVED.value, "confidence": 0.95},
    )

    result = asyncio.run(agent.execute(context, memory))

    summary = context.metadata["supervisor_summary"]
    assert "fraud_agent" in summary["failed_agents"]
    assert summary["final_decision"] == DecisionType.HUMAN_REVIEW.value
    assert summary["overridden"] is True
    assert result.status == "SUCCESS"
