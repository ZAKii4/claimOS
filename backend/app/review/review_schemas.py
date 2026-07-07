from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class ReviewSessionBase(BaseModel):
    claim_id: str
    queue_name: str
    priority: int
    sla_deadline: Optional[datetime] = None
    evidence_graph: dict
    validation_report: dict
    decision_reason: str


class ReviewSessionCreate(ReviewSessionBase):
    pass


class ReviewSessionOut(ReviewSessionBase):
    id: str
    status: str
    locked_by: Optional[str]
    locked_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CorrectionPayload(BaseModel):
    action: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    reason: str


class ActionResponse(BaseModel):
    status: str
    message: str
