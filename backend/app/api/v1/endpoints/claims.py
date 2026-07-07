"""
Claims CRUD endpoints.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.v1.dependencies import get_claim_service, get_pagination
from app.schemas.claim import ClaimCreate, ClaimRead, ClaimSummary
from app.schemas.common import PaginatedResponse
from app.services.claim_service import ClaimService
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/claims", tags=["Claims"])


@router.post(
    "",
    response_model=ClaimRead,
    status_code=201,
    summary="Create Claim",
    description="Register a new claim file in the system.",
)
def create_claim(
    data: ClaimCreate,
    service: ClaimService = Depends(get_claim_service),
) -> ClaimRead:
    return service.create_claim(data)


@router.get(
    "",
    response_model=PaginatedResponse[ClaimSummary],
    summary="List Claims",
    description="Retrieve a paginated list of claims, optionally filtered by status.",
)
def list_claims(
    pagination: PaginationParams = Depends(get_pagination),
    status: str | None = Query(None, description="Filter by status code (e.g. INGESTED, VALIDATING)."),
    service: ClaimService = Depends(get_claim_service),
) -> PaginatedResponse[ClaimSummary]:
    return service.list_claims(pagination, status=status)


@router.get(
    "/{claim_id}",
    response_model=ClaimRead,
    summary="Get Claim",
    description="Retrieve a single claim by its UUID.",
)
def get_claim(
    claim_id: UUID,
    service: ClaimService = Depends(get_claim_service),
) -> ClaimRead:
    return service.get_claim(claim_id)
