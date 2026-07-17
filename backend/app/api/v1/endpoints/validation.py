import uuid
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from app.api.v1.dependencies import get_current_operator, get_validation_service
from app.engines.evidence_graph.models import EvidenceGraphResult
from app.models.operator import Operator
from app.services.validation_service import ValidationService

router = APIRouter(prefix="/claims", tags=["Validation"])


@router.get("/{claim_id}/validation")
def get_validation_report(
    claim_id: uuid.UUID,
    service: ValidationService = Depends(get_validation_service),
    _operator: Operator = Depends(get_current_operator),
):
    """
    Retrieves the latest Validation Report for the claim.
    """
    return service.get_validation_report(claim_id)


@router.get("/{claim_id}/validation/issues")
def get_validation_issues(
    claim_id: uuid.UUID,
    severity: Optional[str] = None,
    service: ValidationService = Depends(get_validation_service),
    _operator: Operator = Depends(get_current_operator),
):
    """
    Retrieves issues filtered by severity.
    """
    return service.get_validation_issues(claim_id, severity)


@router.get("/{claim_id}/validation/statistics")
def get_validation_statistics(
    claim_id: uuid.UUID,
    service: ValidationService = Depends(get_validation_service),
    _operator: Operator = Depends(get_current_operator),
):
    """
    Retrieves statistics.
    """
    return service.get_validation_statistics(claim_id)


@router.post("/{claim_id}/validation/run")
def run_validation(
    claim_id: uuid.UUID,
    graph: EvidenceGraphResult,
    service: ValidationService = Depends(get_validation_service),
    _operator: Operator = Depends(get_current_operator),
):
    """
    Triggers the validation engine on the provided Evidence Graph.
    """
    try:
        return service.run_validation(claim_id, graph)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
