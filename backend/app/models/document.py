"""
Document and document page models.

Maps to ``claim_document`` and ``document_page`` from ``002_core_domain.sql``.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ClaimDocument(Base):
    __tablename__ = "claim_document"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claim_file.id", ondelete="CASCADE"), nullable=False,
    )
    document_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_type.id"), nullable=False,
    )
    classification_confidence: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4), nullable=True,
    )
    page_range_start: Mapped[int] = mapped_column(Integer, nullable=False)
    page_range_end: Mapped[int] = mapped_column(Integer, nullable=False)
    language: Mapped[str] = mapped_column(String(8), nullable=False, default="fr")
    is_duplicate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    duplicate_of_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claim_document.id"), nullable=True,
    )
    storage_uri: Mapped[str] = mapped_column(Text, nullable=False)
    document_role: Mapped[str | None] = mapped_column(
        String(32), nullable=True,
        doc="Party this document belongs to (OWN_VEHICLE, ADVERSE_VEHICLE, POLICY_HOLDER, "
        "VICTIM) — set by whoever routes the claim's documents; feeds FormMappingEngine.",
    )
    extracted_data: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        doc="Document-level ExtractionResult (merged across pages), as produced by the "
        "document processing pipeline's BusinessExtractionStep.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()",
    )

    __table_args__ = (
        CheckConstraint("page_range_start >= 1", name="chk_page_start"),
        CheckConstraint("page_range_end >= 1", name="chk_page_end"),
        CheckConstraint("page_range_end >= page_range_start", name="chk_page_range"),
        CheckConstraint("duplicate_of_id IS DISTINCT FROM id", name="chk_dup_self"),
        CheckConstraint(
            "classification_confidence BETWEEN 0 AND 1",
            name="chk_doc_confidence",
        ),
    )

    # Relationships
    claim = relationship("ClaimFile", back_populates="documents")
    document_type = relationship("DocumentType", lazy="joined")
    pages = relationship("DocumentPage", back_populates="document", lazy="select")
    duplicate_of = relationship("ClaimDocument", remote_side="ClaimDocument.id", lazy="select")


class DocumentPage(Base):
    __tablename__ = "document_page"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claim_document.id", ondelete="CASCADE"), nullable=False,
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    original_page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    image_uri: Mapped[str] = mapped_column(Text, nullable=False)
    ocr_hocr_uri: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        doc="No pipeline step produces an hOCR file today (OCR output is stored as "
        "structured JSON) — left null rather than forced.",
    )
    orientation_corrected_deg: Mapped[int | None] = mapped_column(Integer, default=0)
    resolution_dpi: Mapped[int] = mapped_column(Integer, nullable=False)
    quality_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    is_missing_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()",
    )

    __table_args__ = (
        UniqueConstraint("document_id", "page_number", name="uq_doc_page"),
        CheckConstraint("page_number >= 1", name="chk_page_number"),
        CheckConstraint("original_page_number >= 1", name="chk_orig_page_number"),
        CheckConstraint("quality_score BETWEEN 0 AND 1", name="chk_quality_score"),
    )

    # Relationships
    document = relationship("ClaimDocument", back_populates="pages")
