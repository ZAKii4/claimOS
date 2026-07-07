from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class DecisionType(str, Enum):
    AUTO_APPROVED = "AUTO_APPROVED"
    AUTO_REJECTED = "AUTO_REJECTED"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    FRAUD_REVIEW = "FRAUD_REVIEW"
    REQUEST_MORE_DOCUMENTS = "REQUEST_MORE_DOCUMENTS"
    PENDING = "PENDING"
    ESCALATED = "ESCALATED"


class QueueName(str, Enum):
    AUTO_PROCESSING = "QUEUE_AUTO_PROCESSING"
    HUMAN_REVIEW = "QUEUE_HUMAN_REVIEW"
    FRAUD = "QUEUE_FRAUD"
    MEDICAL_EXPERT = "QUEUE_MEDICAL_EXPERT"
    LEGAL_EXPERT = "QUEUE_LEGAL_EXPERT"
    VEHICLE_EXPERT = "QUEUE_VEHICLE_EXPERT"
    CUSTOMER_SERVICE = "QUEUE_CUSTOMER_SERVICE"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DecisionAuditEntry(BaseModel):
    id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    actor: str = "SYSTEM"
    strategy_used: str
    rules_applied: list[str] = Field(default_factory=list)
    reason: str
    decision: DecisionType
    policy_version: str


class DecisionResult(BaseModel):
    decision_id: str
    claim_id: str
    decision: DecisionType
    reason: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    explanations: list[str] = Field(default_factory=list)
    applied_rules: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    routing: Optional[QueueName] = None
    priority: int = 0
    sla_deadline_hours: Optional[int] = None
    audit_entries: list[DecisionAuditEntry] = Field(default_factory=list)
    execution_time_ms: int = 0
    risk_level: RiskLevel = RiskLevel.MEDIUM
    created_at: datetime = Field(default_factory=datetime.utcnow)
