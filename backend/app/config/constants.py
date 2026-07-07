"""
Business constants and Python enums mirroring the SQL lookup tables.

These enums provide type-safe references to lookup codes throughout
the codebase. They must stay in sync with the seed data in
database/migrations/001_lookup_tables.sql.
"""

from enum import StrEnum


# ── Claim ────────────────────────────────────────────────────────────────────

class ClaimTypeCode(StrEnum):
    AUTO_LIABILITY = "AUTO_LIABILITY"
    BODILY_INJURY = "BODILY_INJURY"
    PROPERTY_DAMAGE = "PROPERTY_DAMAGE"
    MIXED = "MIXED"
    THEFT = "THEFT"
    NATURAL_DISASTER = "NATURAL_DISASTER"
    FIRE = "FIRE"
    GLASS_BREAKAGE = "GLASS_BREAKAGE"


class ClaimStatusCode(StrEnum):
    INGESTED = "INGESTED"
    PREPROCESSING = "PREPROCESSING"
    OCR_IN_PROGRESS = "OCR_IN_PROGRESS"
    CLASSIFYING = "CLASSIFYING"
    EXTRACTING = "EXTRACTING"
    VALIDATING = "VALIDATING"
    AWAITING_REVIEW = "AWAITING_REVIEW"
    PENDING_DOCUMENTS = "PENDING_DOCUMENTS"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


# ── Document ─────────────────────────────────────────────────────────────────

class DocumentTypeCode(StrEnum):
    POLICE_REPORT = "POLICE_REPORT"
    CONSTAT_AMIABLE = "CONSTAT_AMIABLE"
    MEDICAL_CERTIFICATE = "MEDICAL_CERTIFICATE"
    MEDICAL_BILL = "MEDICAL_BILL"
    REPAIR_ESTIMATE = "REPAIR_ESTIMATE"
    REPAIR_INVOICE = "REPAIR_INVOICE"
    IDENTITY_CARD = "IDENTITY_CARD"
    DRIVING_LICENSE = "DRIVING_LICENSE"
    VEHICLE_REGISTRATION = "VEHICLE_REGISTRATION"
    INSURANCE_ATTESTATION = "INSURANCE_ATTESTATION"
    EXPERT_REPORT = "EXPERT_REPORT"
    DELEGATION_OF_AUTHORITY = "DELEGATION_OF_AUTHORITY"
    PHOTO_EVIDENCE = "PHOTO_EVIDENCE"
    CORRESPONDENCE = "CORRESPONDENCE"
    OTHER = "OTHER"


# ── Parties ──────────────────────────────────────────────────────────────────

class PartyRoleCode(StrEnum):
    POLICYHOLDER = "POLICYHOLDER"
    DRIVER = "DRIVER"
    VICTIM = "VICTIM"
    WITNESS = "WITNESS"
    THIRD_PARTY_DRIVER = "THIRD_PARTY_DRIVER"
    THIRD_PARTY_PASSENGER = "THIRD_PARTY_PASSENGER"
    PEDESTRIAN = "PEDESTRIAN"
    LEGAL_REPRESENTATIVE = "LEGAL_REPRESENTATIVE"
    BENEFICIARY = "BENEFICIARY"


# ── Extraction ───────────────────────────────────────────────────────────────

class ExtractionMethodCode(StrEnum):
    OCR_DIRECT = "OCR_DIRECT"
    LLM_FUZZY_MATCH = "LLM_FUZZY_MATCH"
    LLM_SEMANTIC_INFERENCE = "LLM_SEMANTIC_INFERENCE"
    VLM_VISUAL_READ = "VLM_VISUAL_READ"
    HUMAN_MANUAL = "HUMAN_MANUAL"
    DB_LOOKUP = "DB_LOOKUP"
    SUPER_RESOLUTION_OCR = "SUPER_RESOLUTION_OCR"
    DAMAGE_INFERRED = "DAMAGE_INFERRED"


# ── Audit Events ─────────────────────────────────────────────────────────────

class EventTypeCode(StrEnum):
    CLAIM_INGESTED = "CLAIM_INGESTED"
    DOCUMENT_NORMALIZED = "DOCUMENT_NORMALIZED"
    DOCUMENT_CLASSIFIED = "DOCUMENT_CLASSIFIED"
    ENTITY_EXTRACTED = "ENTITY_EXTRACTED"
    FIELD_CORRECTED = "FIELD_CORRECTED"
    DECISION_RENDERED = "DECISION_RENDERED"
    DECISION_OVERRIDDEN = "DECISION_OVERRIDDEN"
    DISCREPANCY_DETECTED = "DISCREPANCY_DETECTED"
    DISCREPANCY_RESOLVED = "DISCREPANCY_RESOLVED"
    CLAIM_VALIDATED = "CLAIM_VALIDATED"
    CLAIM_REJECTED = "CLAIM_REJECTED"
    DOCUMENT_REQUESTED = "DOCUMENT_REQUESTED"
    CLAIM_REOPENED = "CLAIM_REOPENED"
    OPERATOR_ASSIGNED = "OPERATOR_ASSIGNED"
    POLICY_VERIFIED = "POLICY_VERIFIED"


# ── Validation ───────────────────────────────────────────────────────────────

class FlagReasonCode(StrEnum):
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    DAMAGE_INFERRED = "DAMAGE_INFERRED"
    DB_MISMATCH = "DB_MISMATCH"
    MISSING_BBOX = "MISSING_BBOX"
    ILLEGIBLE_SOURCE = "ILLEGIBLE_SOURCE"
    MULTI_VALUE = "MULTI_VALUE"


class DiscrepancyTypeCode(StrEnum):
    DATE_CONFLICT = "DATE_CONFLICT"
    LIABILITY_MISMATCH = "LIABILITY_MISMATCH"
    VEHICLE_POLICY_MISMATCH = "VEHICLE_POLICY_MISMATCH"
    MEDICAL_INCONSISTENCY = "MEDICAL_INCONSISTENCY"
    IDENTITY_MISMATCH = "IDENTITY_MISMATCH"
    AMOUNT_DISCREPANCY = "AMOUNT_DISCREPANCY"
    DUPLICATE_CLAIM = "DUPLICATE_CLAIM"
    POLICY_EXPIRED_AT_LOSS_DATE = "POLICY_EXPIRED_AT_LOSS_DATE"


# ── Vehicle ──────────────────────────────────────────────────────────────────

class FuelType(StrEnum):
    GASOLINE = "GASOLINE"
    DIESEL = "DIESEL"
    ELECTRIC = "ELECTRIC"
    HYBRID = "HYBRID"
    LPG = "LPG"
    UNKNOWN = "UNKNOWN"


class DamageSeverityCode(StrEnum):
    MINOR = "MINOR"
    MODERATE = "MODERATE"
    SEVERE = "SEVERE"
    TOTAL_LOSS = "TOTAL_LOSS"


# ── Medical ──────────────────────────────────────────────────────────────────

class PrognosisCode(StrEnum):
    FULL_RECOVERY = "FULL_RECOVERY"
    PARTIAL_DISABILITY = "PARTIAL_DISABILITY"
    PERMANENT_DISABILITY = "PERMANENT_DISABILITY"
    UNDER_TREATMENT = "UNDER_TREATMENT"
    CONSOLIDATION_PENDING = "CONSOLIDATION_PENDING"


# ── Decision ─────────────────────────────────────────────────────────────────

class ValidationDecisionCode(StrEnum):
    STP_APPROVED = "STP_APPROVED"
    HITL_REVIEW = "HITL_REVIEW"
    REJECTED = "REJECTED"
    PENDING_DOCUMENTS = "PENDING_DOCUMENTS"


class DecisionActorType(StrEnum):
    AI_ENGINE = "AI_ENGINE"
    HUMAN_OPERATOR = "HUMAN_OPERATOR"


# ── Versioning Origin ────────────────────────────────────────────────────────

class VersionOrigin(StrEnum):
    AI_EXTRACTION = "AI_EXTRACTION"
    HUMAN_CORRECTION = "HUMAN_CORRECTION"
    DB_ENRICHMENT = "DB_ENRICHMENT"


# ── Operator ─────────────────────────────────────────────────────────────────

class OperatorRoleCode(StrEnum):
    REVIEWER = "REVIEWER"
    SENIOR_REVIEWER = "SENIOR_REVIEWER"
    SUPERVISOR = "SUPERVISOR"
    ADMIN = "ADMIN"
    SYSTEM = "SYSTEM"


# ── Policy ───────────────────────────────────────────────────────────────────

class PolicyStatus(StrEnum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    SUSPENDED = "SUSPENDED"


class ProductTypeCode(StrEnum):
    AUTO_TPL = "AUTO_TPL"
    AUTO_COMPREHENSIVE = "AUTO_COMPREHENSIVE"
    AUTO_FIRE_THEFT = "AUTO_FIRE_THEFT"
    FLEET = "FLEET"


# ── Audit Actor ──────────────────────────────────────────────────────────────

class ActorType(StrEnum):
    SYSTEM = "SYSTEM"
    AI_AGENT = "AI_AGENT"
    HUMAN_OPERATOR = "HUMAN_OPERATOR"


# ── Alcohol Test ─────────────────────────────────────────────────────────────

class AlcoholTestResult(StrEnum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NOT_TESTED = "NOT_TESTED"


# ── Severity (for discrepancies) ─────────────────────────────────────────────

class DiscrepancySeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


# ── Thresholds ───────────────────────────────────────────────────────────────

# Minimum confidence for a field to be accepted without human review.
CONFIDENCE_THRESHOLD_OCR: float = 0.85
CONFIDENCE_THRESHOLD_CLASSIFICATION: float = 0.90
CONFIDENCE_THRESHOLD_COMPOSITE: float = 0.85

# ── Pagination defaults ─────────────────────────────────────────────────────

DEFAULT_PAGE_SIZE: int = 20
MAX_PAGE_SIZE: int = 100
