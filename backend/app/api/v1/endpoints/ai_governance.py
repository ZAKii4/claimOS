from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any

from app.model_registry.registry import ModelRegistry
from app.model_registry.lifecycle import LifecycleManager
from app.model_registry.evaluation import EvaluationEngine
from app.model_registry.responsible import ResponsibleAIManager
from app.model_registry.risk import AIRiskEngine
from app.model_registry.compliance import AIComplianceManager
from app.model_registry.prompt_governance import PromptGovernanceManager
from app.model_registry.dataset_governance import DatasetGovernanceManager
from app.model_registry.monitoring import ModelMonitoringEngine
from app.model_registry.approval import ApprovalWorkflowEngine
from app.model_registry.explainability import EnterpriseExplainabilityEngine
from app.model_registry.scorecard import AIScorecardEngine

router = APIRouter(prefix="/ai-governance", tags=["AI Governance"])

class RegisterModelReq(BaseModel):
    name: str
    version: str
    provider: str
    m_type: str

class ApprovalReq(BaseModel):
    model_id: str
    reviewer: str

@router.get("/models")
def get_models():
    return ModelRegistry.get_all_models()

@router.post("/models/register")
def register_model(req: RegisterModelReq):
    return ModelRegistry.register_model(req.name, req.version, req.provider, req.m_type)

@router.get("/evaluations")
def get_evaluations(model_id: str):
    return EvaluationEngine.evaluate(model_id)

@router.get("/monitoring")
def get_monitoring(model_id: str):
    return ModelMonitoringEngine.get_metrics(model_id)

@router.get("/scorecards")
def get_scorecard(model_id: str):
    return AIScorecardEngine.generate_scorecard(model_id)

@router.get("/compliance")
def get_compliance(model_id: str):
    return AIComplianceManager.run_compliance_check(model_id)

@router.get("/datasets")
def get_datasets():
    return DatasetGovernanceManager.get_all()

@router.get("/prompts")
def get_prompts():
    return PromptGovernanceManager.get_all()

@router.post("/approval")
def post_approval(req: ApprovalReq):
    return {"success": ApprovalWorkflowEngine.approve(req.model_id, req.reviewer)}

@router.post("/rollback")
def post_rollback(model_id: str):
    return {"success": LifecycleManager.transition_model(model_id, "ROLLED_BACK")}

@router.get("/risks")
def get_risks(model_id: str):
    return AIRiskEngine.categorize_risk(model_id)

@router.get("/responsible")
def get_responsible_ai(model_id: str):
    return ResponsibleAIManager.calculate_metrics(model_id)
