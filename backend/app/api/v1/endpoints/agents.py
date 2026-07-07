from fastapi import APIRouter
from app.agents.manager import AgentManager
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

# Phase 24 specific imports
from app.agents.core.goals import Goal
from app.agents.core.planning import PlanningEngine
from app.agents.reasoning.reasoner import ReasoningEngine, ReasoningStrategy, ReasoningResult
from app.agents.collaboration.workspace import CollaborationManager, Observation
from app.agents.collaboration.negotiation import NegotiationEngine, AgentProposal, NegotiationStrategy
from app.agents.memory.memory import MemoryManager, MemoryType
from app.agents.memory.reflection import ReflectionEngine

router = APIRouter(prefix="/agents", tags=["Multi-Agent Platform & Cognitive AI"])
manager = AgentManager()


class RunRequest(BaseModel):
    claim_id: str
    raw_data: Dict[str, Any]


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


# ──────────────────────────────────────────────────────────
# Phase 24: Enterprise Agentic AI Endpoints
# ──────────────────────────────────────────────────────────

class GoalRequest(BaseModel):
    tenant_id: str
    objective: str

class NegotiateRequest(BaseModel):
    tenant_id: str
    proposals: List[Dict[str, Any]] # e.g. [{"agent_id": "a", "decision": "x", "confidence": 0.9}]
    strategy: NegotiationStrategy = NegotiationStrategy.WEIGHTED_CONFIDENCE

class ReflectionRequest(BaseModel):
    tenant_id: str
    agent_id: str
    context_id: str
    outcome: str
    expected_outcome: str


@router.post("/plans/generate")
def generate_plan(req: GoalRequest):
    """Generates a structured execution plan from a high-level objective."""
    return PlanningEngine.generate_plan(req.tenant_id, req.objective)


@router.get("/reasoning/{tenant_id}")
def get_reasoning(tenant_id: str, strategy: NegotiationStrategy = ReasoningStrategy.RULE_BASED, fraud_score: int = 50):
    """Performs an autonomous reasoning step."""
    return ReasoningEngine.reason(
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
