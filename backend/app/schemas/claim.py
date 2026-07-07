"""
Claim-related Pydantic schemas (DTOs).
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ClaimCreate(BaseModel):
    """Schema for creating a new claim file."""

    external_ref: str = Field(..., max_length=64, description="External reference number.")
    claim_type_id: UUID = Field(..., description="FK to claim_type lookup.")
    date_of_loss: date = Field(..., description="Date the loss occurred.")
    policy_id: UUID | None = Field(None, description="FK to insurance_policy (optional at ingestion).")


class ClaimSummary(BaseModel):
    """Lightweight claim representation for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    external_ref: str
    date_of_loss: date
    date_received: datetime
    stp_eligible: bool
    composite_confidence: Decimal | None = None

    # Denormalised lookup codes for display
    claim_type_code: str | None = None
    status_code: str | None = None


class ClaimRead(BaseModel):
    """Detailed claim representation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    external_ref: str
    policy_id: UUID | None = None
    claim_type_id: UUID
    date_of_loss: date
    date_received: datetime
    composite_confidence: Decimal | None = None
    status_id: UUID
    stp_eligible: bool
    created_at: datetime
    updated_at: datetime

    # Denormalised lookup codes
    claim_type_code: str | None = None
    status_code: str | None = None
