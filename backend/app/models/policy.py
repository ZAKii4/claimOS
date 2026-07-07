"""
Insurance policy model.

Maps to the ``insurance_policy`` table from ``002_core_domain.sql``.
"""

import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class InsurancePolicy(TimestampMixin, Base):
    __tablename__ = "insurance_policy"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    policy_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    insurer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("insurer.id"), nullable=False,
    )
    product_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_type.id"), nullable=False,
    )
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE")
    policyholder_party_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claim_party.id"), nullable=True,
    )

    __table_args__ = (
        CheckConstraint("expiry_date > effective_date", name="chk_policy_dates"),
        CheckConstraint(
            "status IN ('ACTIVE','EXPIRED','CANCELLED','SUSPENDED')",
            name="chk_policy_status",
        ),
    )

    # Relationships
    insurer = relationship("Insurer", lazy="joined")
    product_type = relationship("ProductType", lazy="joined")
    policyholder = relationship("ClaimParty", lazy="select", foreign_keys=[policyholder_party_id])
