"""
Document-specific repository.

Extends ``BaseRepository`` with domain queries for claim documents.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.document import ClaimDocument
from app.repositories.base_repository import BaseRepository


class DocumentRepository(BaseRepository[ClaimDocument]):
    """Repository for ``ClaimDocument`` entities."""

    def __init__(self, db: Session) -> None:
        super().__init__(ClaimDocument, db)

    def get_by_claim(self, claim_id: UUID) -> list[ClaimDocument]:
        """Return all documents belonging to a claim."""
        stmt = (
            select(ClaimDocument)
            .where(ClaimDocument.claim_id == claim_id)
            .order_by(ClaimDocument.page_range_start)
        )
        return list(self._db.scalars(stmt).all())

    def get_with_pages(self, document_id: UUID) -> ClaimDocument | None:
        """Load a document eagerly with all its pages."""
        stmt = (
            select(ClaimDocument)
            .options(joinedload(ClaimDocument.pages))
            .where(ClaimDocument.id == document_id)
        )
        return self._db.scalars(stmt).unique().first()
