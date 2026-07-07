from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from app.agentic_ai.core.registry import AgentRegistry, AgentProfile
from app.agentic_ai.core.supervisor import SupervisorEngine
from app.agentic_ai.core.tools import LocalToolEngine
from app.agentic_ai.cognitive.compression import ContextCompressionEngine
from app.agentic_ai.cognitive.evaluation import EvaluationEngine
from app.agentic_ai.cognitive.prompts import PromptRepository, PromptVersion

router = APIRouter(prefix="/agentic-ai", tags=["Local Agentic AI Platform"])


class ToolRequest(BaseModel):
    agent_name: str
    tool_name: str
    parameters: Dict[str, Any]


class CompressionRequest(BaseModel):
    items: List[Dict[str, Any]]
    max_tokens: int


class EvaluationRequest(BaseModel):
    response: str
    expected_context: str


class PromptRequest(BaseModel):
    agent_name: str
    content: str
    version_tag: str


class RollbackRequest(BaseModel):
    agent_name: str
    version_tag: str


@router.get("/agents", response_model=List[AgentProfile])
def get_agents():
    """Lists all cognitive agents."""
    return AgentRegistry.list_agents()


@router.post("/teams/generate")
def build_team(claim_context: Dict[str, Any]):
    """Dynamically builds a team of agents according to the claim context."""
    return {"team": SupervisorEngine.build_team(claim_context)}


@router.post("/tools/run")
def run_tool(req: ToolRequest):
    """Executes a local claimOS tool."""
    return LocalToolEngine.invoke_tool(req.agent_name, req.tool_name, req.parameters)


@router.post("/context/compress")
def compress_context(req: CompressionRequest):
    """Compresses context to fit LLM window and save memory."""
    return ContextCompressionEngine.compress_context(req.items, req.max_tokens)


@router.post("/evaluation")
def evaluate_response(req: EvaluationRequest):
    """Evaluates the quality of a response (hallucination, grounding)."""
    return EvaluationEngine.evaluate_response(req.response, req.expected_context)


@router.post("/prompts")
def add_prompt(req: PromptRequest):
    """Versions and stores a new prompt for an agent."""
    return PromptRepository.add_prompt(req.agent_name, req.content, req.version_tag)


@router.get("/prompts/{agent_name}")
def get_prompt(agent_name: str):
    """Gets the currently active prompt for an agent."""
    p = PromptRepository.get_active_prompt(agent_name)
    if not p:
        raise HTTPException(status_code=404, detail="No active prompt found")
    return p


@router.post("/prompts/rollback")
def rollback_prompt(req: RollbackRequest):
    """Rolls back to a previous prompt version."""
    success = PromptRepository.rollback_prompt(req.agent_name, req.version_tag)
    if not success:
        raise HTTPException(status_code=404, detail="Prompt version not found")
    return {"status": "Rollback successful"}
