"""
Police report models with temporal versioning.

Maps to ``police_report``, ``police_report_version``, and
``police_party_statement`` from ``004_medical_legal.sql``.
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
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PoliceReport(Base):
    """Stable identity of a police report within a claim."""

    __tablename__ = "police_report"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claim_file.id", ondelete="CASCADE"), nullable=False,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claim_document.id"), nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()",
    )

    # Relationships
    document = relationship("ClaimDocument", lazy="select")
    versions = relationship(
        "PoliceReportVersion", back_populates="report", lazy="select",
        order_by="PoliceReportVersion.version.desc()",
    )
    statements = relationship("PolicePartyStatement", back_populates="report", lazy="select")


class PoliceReportVersion(Base):
    """Immutable version snapshot of a police report's extracted data."""

    __tablename__ = "police_report_version"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("police_report.id", ondelete="CASCADE"), nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    origin: Mapped[str] = mapped_column(String(16), nullable=False)
    operator_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("operator.id"), nullable=True,
    )

    # Typed, normalized fields
    report_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    report_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    station_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    accident_location: Mapped[str | None] = mapped_column(String(512), nullable=True)
    accident_datetime: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    weather_condition_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("weather_condition.id"), nullable=True,
    )
    road_condition_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("road_condition.id"), nullable=True,
    )
    liability_split_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    alcohol_test_result: Mapped[str | None] = mapped_column(String(16), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()",
    )

    __table_args__ = (
        UniqueConstraint("report_id", "version", name="uq_pr_version"),
        CheckConstraint("version >= 1", name="chk_pr_version"),
        CheckConstraint(
            "origin IN ('AI_EXTRACTION','HUMAN_CORRECTION','DB_ENRICHMENT')",
            name="chk_pr_origin",
        ),
        CheckConstraint(
            "alcohol_test_result IN ('POSITIVE','NEGATIVE','NOT_TESTED') OR alcohol_test_result IS NULL",
            name="chk_alcohol_test",
        ),
    )

    # Relationships
    report = relationship("PoliceReport", back_populates="versions")
    operator = relationship("Operator", lazy="select")
    weather_condition = relationship("WeatherCondition", lazy="joined")
    road_condition = relationship("RoadCondition", lazy="joined")


class PolicePartyStatement(Base):
    """Statement made by a party in the context of a police report."""

    __tablename__ = "police_party_statement"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("police_report.id", ondelete="CASCADE"), nullable=False,
    )
    party_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claim_party.id"), nullable=False,
    )
    statement_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_consistent_with_facts: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()",
    )

    # Relationships
    report = relationship("PoliceReport", back_populates="statements")
    party = relationship("ClaimParty", lazy="select")
