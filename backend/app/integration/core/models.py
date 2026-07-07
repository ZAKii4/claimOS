from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# ─────────────────────────────────────────────────────
# Events
# ─────────────────────────────────────────────────────

class EventType(str, Enum):
    CLAIM_CREATED = "ClaimCreated"
    CLAIM_UPDATED = "ClaimUpdated"
    CLAIM_APPROVED = "ClaimApproved"
    CLAIM_REJECTED = "ClaimRejected"
    FRAUD_DETECTED = "FraudDetected"
    REVIEW_COMPLETED = "ReviewCompleted"
    PAYMENT_REQUESTED = "PaymentRequested"
    PAYMENT_COMPLETED = "PaymentCompleted"
    DOCUMENT_UPLOADED = "DocumentUploaded"


class IntegrationEvent(BaseModel):
    id: str
    tenant_id: str
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: Dict[str, Any] = Field(default_factory=dict)
    source: str = "claimos"


# ─────────────────────────────────────────────────────
# Webhooks
# ─────────────────────────────────────────────────────

class WebhookConfig(BaseModel):
    id: str
    tenant_id: str
    url: str
    secret: str
    events: List[EventType]
    active: bool = True
    retry_count: int = 3


# ─────────────────────────────────────────────────────
# Notifications
# ─────────────────────────────────────────────────────

class NotificationChannel(str, Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"
    TEAMS = "TEAMS"
    SLACK = "SLACK"
    WEBHOOK = "WEBHOOK"


class Notification(BaseModel):
    id: str
    tenant_id: str
    channel: NotificationChannel
    recipient: str
    template_id: str
    context: Dict[str, Any] = Field(default_factory=dict)
    status: str = "PENDING"
    sent_at: Optional[datetime] = None


# ─────────────────────────────────────────────────────
# Sync
# ─────────────────────────────────────────────────────

class SyncResult(BaseModel):
    id: str
    tenant_id: str
    connector_id: str
    status: str = "SUCCESS"
    records_synced: int = 0
    conflicts: int = 0
    details: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────────────────
# Marketplace
# ─────────────────────────────────────────────────────

class MarketplaceExtensionType(str, Enum):
    OCR_ENGINE = "OCR_ENGINE"
    AI_MODEL = "AI_MODEL"
    FRAUD_RULE = "FRAUD_RULE"
    WORKFLOW = "WORKFLOW"
    DASHBOARD = "DASHBOARD"
    CONNECTOR = "CONNECTOR"
    VALIDATOR = "VALIDATOR"
    KNOWLEDGE_PACK = "KNOWLEDGE_PACK"


class MarketplaceExtension(BaseModel):
    id: str
    name: str
    version: str
    vendor: str
    type: MarketplaceExtensionType
    description: str = ""
    signature: str = ""
    installed: bool = False
