"""
Models package — re-exports all SQLAlchemy models.

Importing this module ensures all models are registered with the
declarative ``Base``, which is required for schema reflection and
relationship resolution.
"""

# Base
# Audit
from app.models.audit import ClaimEvent
from app.models.base import Base, TimestampMixin, uuid_pk
from app.models.claim import ClaimFile
from app.models.document import ClaimDocument, DocumentPage

# Knowledge
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument, TenantEmbedding

# Lookup tables
from app.models.lookups import (
    BodyRegion,
    ClaimStatus,
    ClaimType,
    DamageSeverity,
    DamageZone,
    DiscrepancyType,
    DocumentType,
    EventType,
    ExtractionMethod,
    FlagReason,
    InjuryType,
    Insurer,
    OperatorRole,
    PartyRole,
    ProductType,
    Prognosis,
    RoadCondition,
    WeatherCondition,
)

# Medical & legal
from app.models.medical import MedicalCertificate, MedicalCertVersion, MedicalFinding

# Core domain
from app.models.operator import Operator

# Parties & vehicles
from app.models.party import ClaimParty, PartyVersion
from app.models.police_report import PolicePartyStatement, PoliceReport, PoliceReportVersion
from app.models.policy import InsurancePolicy

# Provenance & validation
from app.models.provenance import FieldProvenance
from app.models.validation import ClaimDiscrepancy, ValidationDecision, ValidationFieldFlag
from app.models.vehicle import ClaimVehicle, VehicleDamage, VehicleVersion

__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    "uuid_pk",
    # Lookups
    "BodyRegion",
    "ClaimStatus",
    "ClaimType",
    "DamageSeverity",
    "DamageZone",
    "DiscrepancyType",
    "DocumentType",
    "EventType",
    "ExtractionMethod",
    "FlagReason",
    "Insurer",
    "InjuryType",
    "OperatorRole",
    "PartyRole",
    "Prognosis",
    "ProductType",
    "RoadCondition",
    "WeatherCondition",
    # Core domain
    "Operator",
    "InsurancePolicy",
    "ClaimFile",
    "ClaimDocument",
    "DocumentPage",
    # Parties & vehicles
    "ClaimParty",
    "PartyVersion",
    "ClaimVehicle",
    "VehicleVersion",
    "VehicleDamage",
    # Medical & legal
    "MedicalCertificate",
    "MedicalCertVersion",
    "MedicalFinding",
    "PoliceReport",
    "PoliceReportVersion",
    "PolicePartyStatement",
    # Provenance & validation
    "FieldProvenance",
    "ValidationDecision",
    "ValidationFieldFlag",
    "ClaimDiscrepancy",
    # Knowledge
    "KnowledgeDocument",
    "KnowledgeChunk",
    "TenantEmbedding",
    # Audit
    "ClaimEvent",
]
