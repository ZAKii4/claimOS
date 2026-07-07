"""
Medical domain models.

Maps to ``medical_certificate``, ``medical_cert_version``, and
``medical_finding`` from ``004_medical_legal.sql``.
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


class MedicalCertificate(Base):
    """Stable identity of a medical certificate within a claim."""

    __tablename__ = "medical_certificate"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claim_file.id", ondelete="CASCADE"), nullable=False,
    )
    party_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claim_party.id"), nullable=False,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claim_document.id"), nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()",
    )

    # Relationships
    party = relationship("ClaimParty", lazy="select")
    document = relationship("ClaimDocument", lazy="select")
    versions = relationship(
        "MedicalCertVersion", back_populates="certificate", lazy="select",
        order_by="MedicalCertVersion.version.desc()",
    )
    findings = relationship("MedicalFinding", back_populates="certificate", lazy="select")


class MedicalCertVersion(Base):
    """Immutable version snapshot of a medical certificate's extracted data."""

    __tablename__ = "medical_cert_version"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    certificate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("medical_certificate.id", ondelete="CASCADE"), nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    origin: Mapped[str] = mapped_column(String(16), nullable=False)
    operator_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("operator.id"), nullable=True,
    )

    # Typed, normalized fields
    issuing_facility: Mapped[str | None] = mapped_column(String(256), nullable=True)
    issuing_doctor: Mapped[str | None] = mapped_column(String(256), nullable=True)
    issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    initial_disability_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hospitalization_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_final: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()",
    )

    __table_args__ = (
        UniqueConstraint("certificate_id", "version", name="uq_medcert_version"),
        CheckConstraint("version >= 1", name="chk_medcert_version"),
        CheckConstraint(
            "origin IN ('AI_EXTRACTION','HUMAN_CORRECTION','DB_ENRICHMENT')",
            name="chk_medcert_origin",
        ),
        CheckConstraint(
            "initial_disability_days >= 0 OR initial_disability_days IS NULL",
            name="chk_disability_days",
        ),
        CheckConstraint(
            "hospitalization_days >= 0 OR hospitalization_days IS NULL",
            name="chk_hosp_days",
        ),
    )

    # Relationships
    certificate = relationship("MedicalCertificate", back_populates="versions")
    operator = relationship("Operator", lazy="select")


class MedicalFinding(Base):
    """Normalized diagnosis or injury linked to a medical certificate."""

    __tablename__ = "medical_finding"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    certificate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("medical_certificate.id", ondelete="CASCADE"), nullable=False,
    )
    icd10_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    body_region_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("body_region.id"), nullable=True,
    )
    injury_type_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("injury_type.id"), nullable=True,
    )
    prognosis_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prognosis.id"), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()",
    )

    # Relationships
    certificate = relationship("MedicalCertificate", back_populates="findings")
    body_region = relationship("BodyRegion", lazy="joined")
    injury_type = relationship("InjuryType", lazy="joined")
    prognosis = relationship("Prognosis", lazy="joined")
