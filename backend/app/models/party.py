"""
Party models with temporal versioning.

Maps to ``claim_party`` and ``party_version`` from ``003_parties_vehicles.sql``.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ClaimParty(Base):
    """Stable identity of a party involved in a claim."""

    __tablename__ = "claim_party"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claim_file.id", ondelete="CASCADE"), nullable=False,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("party_role.id"), nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()",
    )

    # Relationships
    claim = relationship("ClaimFile", back_populates="parties")
    role = relationship("PartyRole", lazy="joined")
    versions = relationship(
        "PartyVersion", back_populates="party", lazy="select",
        order_by="PartyVersion.version.desc()",
    )


class PartyVersion(Base):
    """Immutable version snapshot of a party's data."""

    __tablename__ = "party_version"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    party_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claim_party.id", ondelete="CASCADE"), nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    origin: Mapped[str] = mapped_column(String(16), nullable=False)
    operator_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("operator.id"), nullable=True,
    )

    # Typed, normalized fields
    last_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    national_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(24), nullable=True)
    address_line_1: Mapped[str | None] = mapped_column(String(256), nullable=True)
    address_city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    address_postal_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    address_country_iso: Mapped[str | None] = mapped_column(String(2), nullable=True)
    driving_license_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    driving_license_category: Mapped[str | None] = mapped_column(String(8), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()",
    )

    __table_args__ = (
        UniqueConstraint("party_id", "version", name="uq_party_version"),
        CheckConstraint("version >= 1", name="chk_party_version"),
        CheckConstraint(
            "origin IN ('AI_EXTRACTION','HUMAN_CORRECTION','DB_ENRICHMENT')",
            name="chk_party_origin",
        ),
    )

    # Relationships
    party = relationship("ClaimParty", back_populates="versions")
    operator = relationship("Operator", lazy="select")
