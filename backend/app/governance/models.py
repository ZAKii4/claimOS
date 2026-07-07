from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# ─────────────────────────────────────────────────────
# IAM
# ─────────────────────────────────────────────────────

class Permission(BaseModel):
    resource: str      # e.g. "Claims", "Review", "LLM"
    action: str        # e.g. "Read", "Write", "Delete", "Admin"

    def __hash__(self):
        return hash(f"{self.resource}.{self.action}")

    def __eq__(self, other):
        return isinstance(other, Permission) and self.resource == other.resource and self.action == other.action

    def __str__(self):
        return f"{self.resource}.{self.action}"


class Role(BaseModel):
    name: str
    permissions: List[Permission] = Field(default_factory=list)


class User(BaseModel):
    id: str
    username: str
    email: str = ""
    roles: List[str] = Field(default_factory=list)  # Role names
    attributes: Dict[str, Any] = Field(default_factory=dict)  # For ABAC
    active: bool = True


class Session(BaseModel):
    user_id: str
    token: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


# ─────────────────────────────────────────────────────
# Policy
# ─────────────────────────────────────────────────────

class PolicyDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    WARN = "WARN"


class PolicyRule(BaseModel):
    condition: str       # Expression (evaluated by ExpressionEngine)
    decision: PolicyDecision
    message: str = ""


class Policy(BaseModel):
    id: str
    name: str
    version: int = 1
    rules: List[PolicyRule] = Field(default_factory=list)
    active: bool = True


# ─────────────────────────────────────────────────────
# Audit
# ─────────────────────────────────────────────────────

class AuditEntry(BaseModel):
    id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    actor: str           # user_id or "system"
    action: str          # e.g. "Claims.Read", "Review.Override"
    resource: str = ""
    details: Dict[str, Any] = Field(default_factory=dict)
    prev_hash: str = ""  # Hash of previous entry (chain)
    entry_hash: str = "" # Hash of this entry


# ─────────────────────────────────────────────────────
# PII
# ─────────────────────────────────────────────────────

class PIIDetection(BaseModel):
    pii_type: str        # e.g. "email", "phone", "iban"
    value: str
    confidence: float = 1.0
    start: int = 0
    end: int = 0


# ─────────────────────────────────────────────────────
# Compliance
# ─────────────────────────────────────────────────────

class ComplianceStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


class ComplianceCheck(BaseModel):
    framework: str       # "RGPD", "ISO27001", "SOC2", "NIS2"
    control: str
    status: ComplianceStatus
    justification: str = ""


# ─────────────────────────────────────────────────────
# Retention
# ─────────────────────────────────────────────────────

class RetentionPolicy(BaseModel):
    document_type: str
    retention_days: int = 365 * 5     # 5 years default
    archive_after_days: int = 365 * 2
    legal_hold: bool = False


class RetentionResult(BaseModel):
    document_id: str
    expiration_date: datetime
    archive_date: datetime
    deletion_date: datetime
    legal_hold: bool = False


# ─────────────────────────────────────────────────────
# Encryption
# ─────────────────────────────────────────────────────

class KeyMetadata(BaseModel):
    key_id: str
    algorithm: str
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = True
