import uuid
from fastapi import APIRouter, HTTPException
from typing import Optional

from app.engines.base import EngineContext
from app.engines.validation.manager import ValidationEngine
from app.engines.evidence_graph.models import EvidenceGraphResult

router = APIRouter(prefix="/claims", tags=["Validation"])

engine = ValidationEngine()

@router.get("/{claim_id}/validation")
def get_validation_report(claim_id: str):
    """
    Retrieves the latest Validation Report for the claim.
    MVP Note: For this phase, we return a mock since there's no DB persistence yet.
    """
    return {"message": "Endpoint ready. In production, this will fetch from DB.", "claim_id": claim_id}


@router.get("/{claim_id}/validation/issues")
def get_validation_issues(claim_id: str, severity: Optional[str] = None):
    """
    Retrieves issues filtered by severity.
    """
    return {"message": "Endpoint ready.", "claim_id": claim_id, "filter": severity}


@router.get("/{claim_id}/validation/statistics")
def get_validation_statistics(claim_id: str):
    """
    Retrieves statistics.
    """
    return {"message": "Endpoint ready.", "claim_id": claim_id}


@router.post("/{claim_id}/validation/run")
def run_validation(claim_id: str, graph: EvidenceGraphResult):
    """
    Triggers the validation engine on the provided Evidence Graph.
    """
    context = EngineContext(
        claim_id=claim_id,
        input_data={"evidence_graph_result": graph}
    )
    
    result = engine.process(context)
    if result.status == "SUCCESS":
        return result.output_data["validation_report"]
    else:
        raise HTTPException(status_code=500, detail=result.errors)
