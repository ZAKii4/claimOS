from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.agents.claim_bridge import build_agent_raw_data
from app.agents.collaboration.negotiation import (
    AgentProposal,
    NegotiationEngine,
    NegotiationStrategy,
)
from app.agents.collaboration.workspace import CollaborationManager

# Phase 24 specific imports
from app.agents.core.planning import PlanningEngine
from app.agents.manager import AgentManager
from app.agents.memory.memory import MemoryManager, MemoryType
from app.agents.memory.reflection import ReflectionEngine
from app.agents.reasoning.reasoner import ReasoningEngine, ReasoningStrategy
from app.api.v1.dependencies import get_current_operator, get_document_service
from app.models.operator import Operator
from app.services.document_service import DocumentService

router = APIRouter(prefix="/agents", tags=["Multi-Agent Platform & Cognitive AI"])
manager = AgentManager()

# Claim-scoped: unlike /agents/run (generic, caller builds raw_data by hand),
# this resource lives under a real claim and builds raw_data itself from
# that claim's already-persisted, fused opening form — see
# docs/COURS_05_ORCHESTRATION.md.
claim_agents_router = APIRouter(
    prefix="/claims/{claim_id}/agents", tags=["Multi-Agent Platform & Cognitive AI"]
)


class RunRequest(BaseModel):
    claim_id: str
    raw_data: dict[str, Any]


@router.get("/")
def list_agents():
    """List all registered agents."""
    agents = manager.registry.get_all()
    return {
        id: {"name": agent.name, "version": agent.version, "capabilities": agent.capabilities}
        for id, agent in agents.items()
    }


@router.post("/run")
async def run_agents(request: RunRequest):
    """Run the multi-agent platform for a claim."""
    result = await manager.process_claim(request.claim_id, request.raw_data)
    return result


@router.get("/metrics")
def get_metrics():
    """Get performance metrics for all agents."""
    return manager.monitor.get_metrics()


@claim_agents_router.post(
    "/run",
    summary="Run Multi-Agent Collaboration For This Claim",
    description=(
        "Runs the 6-agent collaboration pipeline (OCR Agent, Extraction Agent, Fraud Agent, "
        "Legal Agent, Decision Agent, Supervisor Agent) on this claim's already-persisted, "
        "fused opening form — the post-extraction reasoning layer that cross-checks, scores "
        "fraud risk, verifies legal coherence, and produces an explainable decision "
        "recommendation. Complementary to (not a replacement for) document ingestion: call "
        "this after the claim has some data, whether from uploaded documents "
        "(POST .../documents) or manual entry (POST .../documents/opening-form/manual)."
    ),
)
async def run_agents_for_claim(
    claim_id: UUID,
    service: DocumentService = Depends(get_document_service),
    _operator: Operator = Depends(get_current_operator),
) -> dict[str, Any]:
    opening_form = service.get_opening_form(claim_id)
    raw_data = build_agent_raw_data(opening_form)
    return await manager.process_claim(str(claim_id), raw_data)


# ──────────────────────────────────────────────────────────
# Phase 24: Enterprise Agentic AI Endpoints
# ──────────────────────────────────────────────────────────

class GoalRequest(BaseModel):
    tenant_id: str
    objective: str

class NegotiateRequest(BaseModel):
    tenant_id: str
    proposals: list[dict[str, Any]] # e.g. [{"agent_id": "a", "decision": "x", "confidence": 0.9}]
    strategy: NegotiationStrategy = NegotiationStrategy.WEIGHTED_CONFIDENCE

class ReflectionRequest(BaseModel):
    tenant_id: str
    agent_id: str
    context_id: str
    outcome: str
    expected_outcome: str


@router.post("/plans/generate")
async def generate_plan(req: GoalRequest):
    """Generates a structured execution plan from a high-level objective via the LLM."""
    return await PlanningEngine.generate_plan(req.tenant_id, req.objective)


@router.get("/reasoning/{tenant_id}")
async def get_reasoning(
    tenant_id: str,
    strategy: NegotiationStrategy = ReasoningStrategy.RULE_BASED,
    fraud_score: int = 50,
):
    """Performs an autonomous reasoning step via the LLM."""
    return await ReasoningEngine.reason(
        tenant_id=tenant_id,
        context={"fraud_score": fraud_score},
        strategy=strategy
    )


@router.get("/collaboration/{tenant_id}/{context_id}")
def get_collaboration_history(tenant_id: str, context_id: str):
    """Gets shared observations from the agent workspace."""
    return CollaborationManager.get_context_observations(tenant_id, context_id)


@router.get("/memory/{tenant_id}/{agent_id}")
def get_agent_memory(tenant_id: str, agent_id: str, m_type: str = "EPISODIC"):
    """Fetches a specific memory type for an agent."""
    return MemoryManager.retrieve(tenant_id, agent_id, MemoryType(m_type))


@router.post("/negotiate")
def trigger_negotiation(req: NegotiateRequest):
    """Triggers conflict resolution between agents."""
    agent_proposals = [
        AgentProposal(p["agent_id"], p["decision"], p["confidence"], p.get("weight", 1.0))
        for p in req.proposals
    ]
    return NegotiationEngine.resolve(req.tenant_id, agent_proposals, req.strategy)


@router.post("/reflection")
def self_evaluate(req: ReflectionRequest):
    """Agent evaluates its own performance and extracts lessons."""
    return ReflectionEngine.evaluate(
        req.tenant_id,
        req.agent_id,
        req.context_id,
        req.outcome,
        req.expected_outcome
    )
