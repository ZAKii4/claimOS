"""
Claim-specific repository.

Extends ``BaseRepository`` with domain queries for claim files.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.claim import ClaimFile
from app.models.lookups import ClaimStatus
from app.repositories.base_repository import BaseRepository


class ClaimRepository(BaseRepository[ClaimFile]):
    """Repository for ``ClaimFile`` entities."""

    def __init__(self, db: Session) -> None:
        super().__init__(ClaimFile, db)

    def get_by_external_ref(self, external_ref: str) -> ClaimFile | None:
        """Find a claim by its external reference number."""
        stmt = select(ClaimFile).where(ClaimFile.external_ref == external_ref)
        return self._db.scalars(stmt).first()

    def get_with_documents(self, claim_id: UUID) -> ClaimFile | None:
        """Load a claim eagerly with its documents."""
        stmt = (
            select(ClaimFile)
            .options(joinedload(ClaimFile.documents))
            .where(ClaimFile.id == claim_id)
        )
        return self._db.scalars(stmt).unique().first()

    def list_by_status(
        self,
        status_code: str,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> list[ClaimFile]:
        """List claims filtered by status code."""
        stmt = (
            select(ClaimFile)
            .join(ClaimStatus, ClaimFile.status_id == ClaimStatus.id)
            .where(ClaimStatus.code == status_code)
            .order_by(ClaimFile.date_received.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self._db.scalars(stmt).all())
