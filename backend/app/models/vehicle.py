"""
Vehicle models with temporal versioning and damage records.

Maps to ``claim_vehicle``, ``vehicle_version``, and ``vehicle_damage``
from ``003_parties_vehicles.sql``.
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
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ClaimVehicle(Base):
    """Stable identity of a vehicle involved in a claim."""

    __tablename__ = "claim_vehicle"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claim_file.id", ondelete="CASCADE"), nullable=False,
    )
    party_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claim_party.id"), nullable=True,
    )
    is_insured_vehicle: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()",
    )

    # Relationships
    claim = relationship("ClaimFile", back_populates="vehicles")
    party = relationship("ClaimParty", lazy="select")
    versions = relationship(
        "VehicleVersion", back_populates="vehicle", lazy="select",
        order_by="VehicleVersion.version.desc()",
    )
    damages = relationship("VehicleDamage", back_populates="vehicle", lazy="select")


class VehicleVersion(Base):
    """Immutable version snapshot of a vehicle's data."""

    __tablename__ = "vehicle_version"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claim_vehicle.id", ondelete="CASCADE"), nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    origin: Mapped[str] = mapped_column(String(16), nullable=False)
    operator_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("operator.id"), nullable=True,
    )

    # Typed, normalized fields
    registration_plate: Mapped[str | None] = mapped_column(String(20), nullable=True)
    vin: Mapped[str | None] = mapped_column(String(17), nullable=True)
    make: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    color: Mapped[str | None] = mapped_column(String(32), nullable=True)
    fuel_type: Mapped[str | None] = mapped_column(String(16), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()",
    )

    __table_args__ = (
        UniqueConstraint("vehicle_id", "version", name="uq_vehicle_version"),
        CheckConstraint("version >= 1", name="chk_vehicle_version"),
        CheckConstraint(
            "origin IN ('AI_EXTRACTION','HUMAN_CORRECTION','DB_ENRICHMENT')",
            name="chk_vehicle_origin",
        ),
        CheckConstraint(
            "fuel_type IN ('GASOLINE','DIESEL','ELECTRIC','HYBRID','LPG','UNKNOWN') OR fuel_type IS NULL",
            name="chk_fuel_type",
        ),
        CheckConstraint("year BETWEEN 1900 AND 2100 OR year IS NULL", name="chk_year"),
    )

    # Relationships
    vehicle = relationship("ClaimVehicle", back_populates="versions")
    operator = relationship("Operator", lazy="select")


class VehicleDamage(Base):
    """Individual damage record for a vehicle."""

    __tablename__ = "vehicle_damage"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claim_vehicle.id", ondelete="CASCADE"), nullable=False,
    )
    damage_zone_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("damage_zone.id"), nullable=False,
    )
    severity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("damage_severity.id"), nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="MAD")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()",
    )

    # Relationships
    vehicle = relationship("ClaimVehicle", back_populates="damages")
    damage_zone = relationship("DamageZone", lazy="joined")
    severity = relationship("DamageSeverity", lazy="joined")
