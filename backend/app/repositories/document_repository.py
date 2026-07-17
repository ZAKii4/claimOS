"""
Document-specific repository.

Extends ``BaseRepository`` with domain queries for claim documents.
"""

import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.document import ClaimDocument
from app.models.lookups import DocumentType
from app.repositories.base_repository import BaseRepository


def _slugify(label: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", label.strip().lower()).strip("_")
    return slug or "unknown_document"


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

    def get_or_create_document_type(self, family: str) -> DocumentType:
        """
        Resolve a ``DocumentType`` lookup row by its family label, creating it
        on first sight.

        The classification engine can predict any family label (it is not
        backed by a pre-seeded fixed vocabulary today), so a strict lookup
        would make ingestion fail on the very first unseen document class.
        No translation source exists yet, so ``label_ar`` defaults to the
        same string as ``label_fr`` rather than being silently blank.
        """
        stmt = select(DocumentType).where(DocumentType.label_fr == family)
        existing = self._db.scalars(stmt).first()
        if existing is not None:
            return existing

        code = _slugify(family)
        stmt = select(DocumentType).where(DocumentType.code == code)
        existing_by_code = self._db.scalars(stmt).first()
        if existing_by_code is not None:
            return existing_by_code

        document_type = DocumentType(code=code, label_fr=family, label_ar=family)
        self._db.add(document_type)
        self._db.flush()
        self._db.refresh(document_type)
        return document_type
