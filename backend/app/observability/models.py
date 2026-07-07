from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class Span(BaseModel):
    id: str
    trace_id: str
    parent_id: Optional[str] = None
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    tags: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class Trace(BaseModel):
    id: str
    claim_id: Optional[str] = None
    start_time: float
    spans: List[Span] = Field(default_factory=list)


class TimelineEvent(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    claim_id: str
    event_type: str # e.g., OCR_STARTED, DECISION_APPROVED
    actor: str # e.g., system, OCRSupervisorAgent, human
    duration_ms: Optional[float] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class HealthState(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


class ComponentHealth(BaseModel):
    name: str
    state: HealthState
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AlertSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class Alert(BaseModel):
    id: str
    category: str
    severity: AlertSeverity
    message: str
    recommended_action: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
