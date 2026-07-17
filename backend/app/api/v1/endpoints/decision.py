from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, Any
from app.api.v1.dependencies import get_current_operator
from app.engines.base import EngineContext
from app.engines.decision.manager import DecisionEngine
from app.models.operator import Operator

router = APIRouter(prefix="/claims", tags=["Decision"])

engine = DecisionEngine()


@router.get("/{claim_id}/decision")
def get_decision(claim_id: str, _operator: Operator = Depends(get_current_operator)):
    """
    Retrieves the final automated Decision for a claim.
    """
    return {"message": "Endpoint ready.", "claim_id": claim_id}


@router.get("/{claim_id}/decision/history")
def get_decision_history(claim_id: str, _operator: Operator = Depends(get_current_operator)):
    """
    Retrieves the history of decisions (e.g. initial auto-reject, followed by human approve).
    """
    return {"message": "Endpoint ready.", "claim_id": claim_id}


@router.get("/{claim_id}/decision/explanations")
def get_decision_explanations(claim_id: str, _operator: Operator = Depends(get_current_operator)):
    """
    Retrieves the plain-text explanations for why the decision was taken.
    """
    return {"message": "Endpoint ready.", "claim_id": claim_id}


@router.get("/{claim_id}/decision/audit")
def get_decision_audit(claim_id: str, _operator: Operator = Depends(get_current_operator)):
    """
    Retrieves the strict audit trail for compliance.
    """
    return {"message": "Endpoint ready.", "claim_id": claim_id}


@router.post("/{claim_id}/decision/run")
def run_decision(claim_id: str, payload: dict, _operator: Operator = Depends(get_current_operator)):
    """
    Triggers the decision engine.
    For MVP, requires 'evidence_graph_result' and 'validation_report' in payload.
    """
    context = EngineContext(
        claim_id=claim_id,
        input_data={
            "evidence_graph_result": payload.get("evidence_graph_result"),
            "validation_report": payload.get("validation_report")
        }
    )
    
    result = engine.process(context)
    if result.status == "SUCCESS":
        return result.output_data["decision_result"]
    else:
        raise HTTPException(status_code=500, detail=result.errors)
