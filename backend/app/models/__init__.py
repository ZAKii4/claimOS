"""
Models package — re-exports all SQLAlchemy models.

Importing this module ensures all models are registered with the
declarative ``Base``, which is required for schema reflection and
relationship resolution.
"""

# Base
from app.models.base import Base, TimestampMixin, uuid_pk

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
    Insurer,
    InjuryType,
    OperatorRole,
    PartyRole,
    Prognosis,
    ProductType,
    RoadCondition,
    WeatherCondition,
)

# Core domain
from app.models.operator import Operator
from app.models.policy import InsurancePolicy
from app.models.claim import ClaimFile
from app.models.document import ClaimDocument, DocumentPage

# Parties & vehicles
from app.models.party import ClaimParty, PartyVersion
from app.models.vehicle import ClaimVehicle, VehicleDamage, VehicleVersion

# Medical & legal
from app.models.medical import MedicalCertificate, MedicalCertVersion, MedicalFinding
from app.models.police_report import PolicePartyStatement, PoliceReport, PoliceReportVersion

# Provenance & validation
from app.models.provenance import FieldProvenance
from app.models.validation import ClaimDiscrepancy, ValidationDecision, ValidationFieldFlag

# Audit
from app.models.audit import ClaimEvent

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
    # Audit
    "ClaimEvent",
]
