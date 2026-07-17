from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any

from app.investigation.workspace import InvestigationWorkspace
from app.investigation.copilot import DecisionCopilotEngine
from app.investigation.navigator import KnowledgeNavigator
from app.investigation.comparison import CaseComparisonEngine
from app.investigation.decision import DecisionIntelligenceEngine
from app.investigation.graph import InteractiveEvidenceGraph
from app.investigation.dashboard import ExecutiveDashboardEngine
from app.investigation.recommendation import RecommendationEngine
from app.investigation.search import EnterpriseSearchEngine

router = APIRouter(prefix="/investigation", tags=["Investigation & Decision Intelligence"])

class ChatReq(BaseModel):
    claim_id: str
    message: str

@router.get("/workspace/{claim_id}")
def get_workspace(claim_id: str):
    return InvestigationWorkspace.get_workspace(claim_id)

@router.post("/copilot/chat")
def copilot_chat(req: ChatReq):
    return DecisionCopilotEngine.chat(req.claim_id, req.message)

@router.get("/navigator/{node_id}")
def navigate_knowledge(node_id: str):
    return KnowledgeNavigator.explore_node(node_id)

@router.get("/compare/{claim_a}/{claim_b}")
def compare_claims(claim_a: str, claim_b: str):
    return CaseComparisonEngine.compare(claim_a, claim_b)

@router.get("/decision/{claim_id}")
def analyze_decision(claim_id: str):
    return DecisionIntelligenceEngine.analyze_decision(claim_id)

@router.get("/graph/{claim_id}")
def get_graph(claim_id: str):
    graph = InteractiveEvidenceGraph.get_graph(claim_id)
    graph["_data_source"] = "illustrative — ignores claim_id, not the real evidence graph engine"
    return graph

@router.get("/dashboard")
def get_dashboard():
    return ExecutiveDashboardEngine.get_dashboard()

@router.get("/recommendations/{claim_id}")
def get_recommendations(claim_id: str):
    return RecommendationEngine.get_recommendations(claim_id)

@router.get("/search")
def search(query: str):
    return EnterpriseSearchEngine.search(query)
