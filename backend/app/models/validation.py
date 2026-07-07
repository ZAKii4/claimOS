"""
Validation and discrepancy models.

Maps to ``validation_decision``, ``validation_field_flag``, and
``claim_discrepancy`` from ``005_provenance_validation_audit.sql``.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ValidationDecision(Base):
    """Routing decision: STP approved, HITL review, rejected, or pending docs."""

    __tablename__ = "validation_decision"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claim_file.id", ondelete="CASCADE"), nullable=False,
    )
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    composite_confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    model_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()",
    )
    decided_by: Mapped[str] = mapped_column(String(16), nullable=False)
    operator_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("operator.id"), nullable=True,
    )

    __table_args__ = (
        CheckConstraint(
            "decision IN ('STP_APPROVED','HITL_REVIEW','REJECTED','PENDING_DOCUMENTS')",
            name="chk_vd_decision",
        ),
        CheckConstraint("composite_confidence BETWEEN 0 AND 1", name="chk_vd_confidence"),
        CheckConstraint(
            "decided_by IN ('AI_ENGINE','HUMAN_OPERATOR')",
            name="chk_vd_decided_by",
        ),
    )

    # Relationships
    claim = relationship("ClaimFile", back_populates="validation_decisions")
    operator = relationship("Operator", lazy="select")
    field_flags = relationship("ValidationFieldFlag", back_populates="decision", lazy="select")


class ValidationFieldFlag(Base):
    """A specific field requiring human attention within a validation decision."""

    __tablename__ = "validation_field_flag"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    decision_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("validation_decision.id", ondelete="CASCADE"), nullable=False,
    )
    entity_table: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    field_name: Mapped[str] = mapped_column(String(64), nullable=False)
    flag_reason_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("flag_reason.id"), nullable=False,
    )
    resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("operator.id"), nullable=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()",
    )

    # Relationships
    decision = relationship("ValidationDecision", back_populates="field_flags")
    flag_reason = relationship("FlagReason", lazy="joined")
    resolver = relationship("Operator", lazy="select")


class ClaimDiscrepancy(Base):
    """Cross-document contradiction detected within a claim."""

    __tablename__ = "claim_discrepancy"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claim_file.id", ondelete="CASCADE"), nullable=False,
    )
    discrepancy_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("discrepancy_type.id"), nullable=False,
    )
    entity_a_table: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_a_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    entity_a_field: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_b_table: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_b_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    entity_b_field: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("operator.id"), nullable=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()",
    )

    __table_args__ = (
        CheckConstraint(
            "severity IN ('INFO','WARNING','CRITICAL')",
            name="chk_disc_severity",
        ),
    )

    # Relationships
    claim = relationship("ClaimFile", back_populates="discrepancies")
    discrepancy_type = relationship("DiscrepancyType", lazy="joined")
    resolver = relationship("Operator", lazy="select")
