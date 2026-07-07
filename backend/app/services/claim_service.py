"""
Claim service — business logic orchestrator for claim files.

This service lives in ``app/services/`` and handles **only** business
logic. It delegates data access to repositories and never performs
AI processing directly (that belongs in ``app/engines/``).
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.config.constants import ClaimStatusCode
from app.models.claim import ClaimFile
from app.models.lookups import ClaimStatus
from app.repositories.claim_repository import ClaimRepository
from app.schemas.claim import ClaimCreate, ClaimRead, ClaimSummary
from app.schemas.common import PaginatedResponse
from app.utils.exceptions import DuplicateEntityError, EntityNotFoundError
from app.utils.pagination import PaginationParams


class ClaimService:
    """
    Orchestrates claim lifecycle operations.

    Responsibilities:
    - Create new claim files
    - Retrieve and list claims
    - Update claim status
    - Enforce business rules
    """

    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = ClaimRepository(db)

    # ── Create ───────────────────────────────────────────────────────────

    def create_claim(self, data: ClaimCreate) -> ClaimRead:
        """
        Create a new claim file.

        Business rules:
        - ``external_ref`` must be unique.
        - Initial status is ``INGESTED``.
        """
        # Check uniqueness
        existing = self._repo.get_by_external_ref(data.external_ref)
        if existing is not None:
            raise DuplicateEntityError("ClaimFile", "external_ref", data.external_ref)

        # Resolve INGESTED status id
        ingested_status = self._resolve_status(ClaimStatusCode.INGESTED)

        claim = ClaimFile(
            external_ref=data.external_ref,
            claim_type_id=data.claim_type_id,
            date_of_loss=data.date_of_loss,
            policy_id=data.policy_id,
            status_id=ingested_status.id,
        )

        claim = self._repo.create(claim)
        self._db.commit()
        self._db.refresh(claim)

        return self._to_read(claim)

    # ── Read ─────────────────────────────────────────────────────────────

    def get_claim(self, claim_id: UUID) -> ClaimRead:
        """Return a single claim by id, or raise ``EntityNotFoundError``."""
        claim = self._repo.get_by_id(claim_id)
        if claim is None:
            raise EntityNotFoundError("ClaimFile", str(claim_id))
        return self._to_read(claim)

    def list_claims(
        self,
        pagination: PaginationParams,
        *,
        status: str | None = None,
    ) -> PaginatedResponse[ClaimSummary]:
        """Return a paginated list of claims, optionally filtered by status."""
        if status:
            items = self._repo.list_by_status(
                status, skip=pagination.skip, limit=pagination.limit,
            )
        else:
            items = self._repo.get_all(skip=pagination.skip, limit=pagination.limit)

        total = self._repo.count()

        return PaginatedResponse[ClaimSummary](
            items=[self._to_summary(c) for c in items],
            total=total,
            skip=pagination.skip,
            limit=pagination.limit,
        )

    # ── Helpers ──────────────────────────────────────────────────────────

    def _resolve_status(self, code: str) -> ClaimStatus:
        """Look up a ClaimStatus by code, raising if not found."""
        from sqlalchemy import select

        stmt = select(ClaimStatus).where(ClaimStatus.code == code)
        status = self._db.scalars(stmt).first()
        if status is None:
            raise EntityNotFoundError("ClaimStatus", code)
        return status

    @staticmethod
    def _to_read(claim: ClaimFile) -> ClaimRead:
        return ClaimRead(
            id=claim.id,
            external_ref=claim.external_ref,
            policy_id=claim.policy_id,
            claim_type_id=claim.claim_type_id,
            date_of_loss=claim.date_of_loss,
            date_received=claim.date_received,
            composite_confidence=claim.composite_confidence,
            status_id=claim.status_id,
            stp_eligible=claim.stp_eligible,
            created_at=claim.created_at,
            updated_at=claim.updated_at,
            claim_type_code=claim.claim_type.code if claim.claim_type else None,
            status_code=claim.status.code if claim.status else None,
        )

    @staticmethod
    def _to_summary(claim: ClaimFile) -> ClaimSummary:
        return ClaimSummary(
            id=claim.id,
            external_ref=claim.external_ref,
            date_of_loss=claim.date_of_loss,
            date_received=claim.date_received,
            stp_eligible=claim.stp_eligible,
            composite_confidence=claim.composite_confidence,
            claim_type_code=claim.claim_type.code if claim.claim_type else None,
            status_code=claim.status.code if claim.status else None,
        )
