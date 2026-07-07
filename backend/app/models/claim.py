"""
Claim file model — the root aggregate of the domain.

Maps to the ``claim_file`` table from ``002_core_domain.sql``.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ClaimFile(TimestampMixin, Base):
    __tablename__ = "claim_file"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    external_ref: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    policy_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("insurance_policy.id"), nullable=True,
    )
    claim_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claim_type.id"), nullable=False,
    )
    date_of_loss: Mapped[date] = mapped_column(Date, nullable=False)
    date_received: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()",
    )
    composite_confidence: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4), nullable=True,
    )
    status_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claim_status.id"), nullable=False,
    )
    stp_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ── Relationships ────────────────────────────────────────────────────
    policy = relationship("InsurancePolicy", lazy="select")
    claim_type = relationship("ClaimType", lazy="joined")
    status = relationship("ClaimStatus", lazy="joined")
    documents = relationship("ClaimDocument", back_populates="claim", lazy="select")
    parties = relationship("ClaimParty", back_populates="claim", lazy="select")
    vehicles = relationship("ClaimVehicle", back_populates="claim", lazy="select")
    events = relationship("ClaimEvent", back_populates="claim", lazy="select")
    discrepancies = relationship("ClaimDiscrepancy", back_populates="claim", lazy="select")
    validation_decisions = relationship("ValidationDecision", back_populates="claim", lazy="select")
