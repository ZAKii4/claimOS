"""
Field provenance model — the anti-hallucination layer.

Maps to ``field_provenance`` from ``005_provenance_validation_audit.sql``.
Every extracted value is traced back to its source document page and
bounding box, with confidence scoring and extraction method metadata.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class FieldProvenance(Base):
    """Links every extracted field value to its source location and confidence."""

    __tablename__ = "field_provenance"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    entity_table: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    field_name: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    source_page_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_page.id"), nullable=True,
    )
    bbox_x1: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox_y1: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox_x2: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox_y2: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extraction_method_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("extraction_method.id"), nullable=False,
    )
    model_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    raw_ocr_token: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()",
    )

    __table_args__ = (
        UniqueConstraint("entity_table", "entity_id", "field_name", name="uq_provenance"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="chk_prov_confidence"),
        CheckConstraint(
            "(bbox_x1 IS NULL AND bbox_y1 IS NULL AND bbox_x2 IS NULL AND bbox_y2 IS NULL) "
            "OR "
            "(bbox_x1 IS NOT NULL AND bbox_y1 IS NOT NULL AND bbox_x2 IS NOT NULL AND bbox_y2 IS NOT NULL)",
            name="chk_bbox_complete",
        ),
        CheckConstraint(
            "bbox_x1 IS NULL OR (bbox_x2 > bbox_x1 AND bbox_y2 > bbox_y1)",
            name="chk_bbox_valid",
        ),
    )

    # Relationships
    source_page = relationship("DocumentPage", lazy="select")
    extraction_method = relationship("ExtractionMethod", lazy="joined")
