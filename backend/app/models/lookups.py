"""
Lookup (reference) table models.

These lightweight models mirror the 14 lookup tables defined in
``database/migrations/001_lookup_tables.sql``.  They are populated
via SQL seed data and are read-only at the application level.
"""

import uuid

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


# ── Helpers ──────────────────────────────────────────────────────────────────

class _CodeLookup(Base):
    """Abstract base for code-only lookup tables."""

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)


class _LabelledLookup(_CodeLookup):
    """Abstract base for lookup tables with bilingual labels (fr/ar)."""

    __abstract__ = True

    label_fr: Mapped[str] = mapped_column(String(128), nullable=False)
    label_ar: Mapped[str] = mapped_column(String(128), nullable=False)


# ── Claim ────────────────────────────────────────────────────────────────────

class ClaimType(_LabelledLookup):
    __tablename__ = "claim_type"


class ClaimStatus(Base):
    __tablename__ = "claim_status"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    is_terminal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


# ── Document ─────────────────────────────────────────────────────────────────

class DocumentType(_LabelledLookup):
    __tablename__ = "document_type"


# ── Parties ──────────────────────────────────────────────────────────────────

class PartyRole(_CodeLookup):
    __tablename__ = "party_role"


# ── Extraction ───────────────────────────────────────────────────────────────

class ExtractionMethod(Base):
    __tablename__ = "extraction_method"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(48), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


# ── Audit ────────────────────────────────────────────────────────────────────

class EventType(_CodeLookup):
    __tablename__ = "event_type"


# ── Validation ───────────────────────────────────────────────────────────────

class FlagReason(Base):
    __tablename__ = "flag_reason"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(48), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class DiscrepancyType(_CodeLookup):
    __tablename__ = "discrepancy_type"


# ── Vehicle ──────────────────────────────────────────────────────────────────

class DamageZone(_CodeLookup):
    __tablename__ = "damage_zone"


class DamageSeverity(_CodeLookup):
    __tablename__ = "damage_severity"


# ── Medical ──────────────────────────────────────────────────────────────────

class BodyRegion(_CodeLookup):
    __tablename__ = "body_region"


class InjuryType(_CodeLookup):
    __tablename__ = "injury_type"


class Prognosis(_CodeLookup):
    __tablename__ = "prognosis"


# ── Weather / Road ───────────────────────────────────────────────────────────

class WeatherCondition(_CodeLookup):
    __tablename__ = "weather_condition"


class RoadCondition(_CodeLookup):
    __tablename__ = "road_condition"


# ── Operator ─────────────────────────────────────────────────────────────────

class OperatorRole(_CodeLookup):
    __tablename__ = "operator_role"


# ── Insurance ────────────────────────────────────────────────────────────────

class ProductType(_LabelledLookup):
    __tablename__ = "product_type"


class Insurer(Base):
    __tablename__ = "insurer"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False, default="MA")
