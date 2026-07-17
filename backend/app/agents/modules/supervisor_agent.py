"""
Supervisor Agent.

Last node of the 6-agent graph (depends on every other agent). Deliberately
makes no LLM call: a supervisor arbitrating between other agents' verdicts
should be deterministic and auditable, not itself a probabilistic opinion.

Its two jobs:
  1. Aggregate every agent's outcome (status, confidence, key artifacts) into
     one summary a human reviewer or the API response can read at a glance.
  2. Apply a final safety net: if DecisionAgent's own confidence was low, or
     any upstream agent failed outright, escalate to HUMAN_REVIEW regardless
     of what DecisionAgent recommended — a low-confidence automated decision
     should never reach a claimant as if it were a confident one.
"""

import time

from app.agents.base import AgentResult, BaseAgent
from app.agents.context import AgentContext
from app.agents.shared_memory import SharedMemory
from app.engines.decision.models import DecisionType

LOW_CONFIDENCE_OVERRIDE_THRESHOLD = 0.4

UPSTREAM_AGENT_IDS = [
    "ocr_supervisor",
    "extraction_agent",
    "fraud_agent",
    "legal_agent",
    "decision_agent",
]


class SupervisorAgent(BaseAgent):
    id = "supervisor_agent"
    name = "Supervisor Agent"
    version = "1.0.0"
    capabilities = ["arbitration", "final_summary"]

    async def plan(self, context: AgentContext, memory: SharedMemory) -> bool:
        return bool(context.decision)

    async def execute(self, context: AgentContext, memory: SharedMemory) -> AgentResult:
        start_time = time.time()

        agent_summaries = {
            agent_id: {
                "ran": bool(memory.get_observations_by_agent(agent_id)),
                "observations": [
                    obs.data for obs in memory.get_observations_by_agent(agent_id)
                ],
            }
            for agent_id in UPSTREAM_AGENT_IDS
        }

        decision = context.decision.get("decision", DecisionType.HUMAN_REVIEW.value)
        decision_confidence = float(context.decision.get("confidence", 0.0))

        failed_agents = [
            agent_id for agent_id, summary in agent_summaries.items() if not summary["ran"]
        ]

        overridden = False
        final_decision = decision
        override_reason = None

        is_low_confidence = decision_confidence < LOW_CONFIDENCE_OVERRIDE_THRESHOLD
        if is_low_confidence and decision != DecisionType.HUMAN_REVIEW.value:
            final_decision = DecisionType.HUMAN_REVIEW.value
            overridden = True
            override_reason = (
                f"Confiance de la décision automatique trop faible "
                f"({decision_confidence:.2f} < {LOW_CONFIDENCE_OVERRIDE_THRESHOLD}) — "
                "arbitrage en faveur d'une révision humaine."
            )
        elif failed_agents and decision != DecisionType.HUMAN_REVIEW.value:
            final_decision = DecisionType.HUMAN_REVIEW.value
            overridden = True
            override_reason = (
                f"Agent(s) n'ayant pas produit de résultat: {', '.join(failed_agents)} — "
                "arbitrage en faveur d'une révision humaine par précaution."
            )

        summary = {
            "final_decision": final_decision,
            "overridden": overridden,
            "override_reason": override_reason,
            "underlying_decision_agent_output": context.decision,
            "agent_summaries": agent_summaries,
            "failed_agents": failed_agents,
        }

        context.metadata["supervisor_summary"] = summary
        memory.add_observation(
            self.id, summary, confidence=1.0 if not overridden else decision_confidence
        )

        return AgentResult(
            status="SUCCESS",
            confidence=1.0,
            execution_time_ms=int((time.time() - start_time) * 1000),
            artifacts=summary,
            messages=[
                f"Final decision: {final_decision}"
                + (f" (overrode {decision} — {override_reason})" if overridden else "")
            ],
        )

    async def validate(self, result: AgentResult) -> bool:
        return result.status == "SUCCESS"
