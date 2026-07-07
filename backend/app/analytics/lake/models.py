from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from datetime import datetime
import uuid


class DataLayer(str, Enum):
    BRONZE = "BRONZE"  # Raw
    SILVER = "SILVER"  # Cleaned / Normalized
    GOLD = "GOLD"      # Aggregated / Business Logic


class LakeRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    layer: DataLayer
    source_type: str  # e.g., "claim", "document", "ocr_result"
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1


class FactRecord(BaseModel):
    """Represents a fact table entry (e.g. a claim creation event, a decision)."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    fact_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    dimensions: Dict[str, str] = Field(default_factory=dict)
    measures: Dict[str, float] = Field(default_factory=dict)


class DataQualityIssue(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    record_id: str
    issue_type: str  # completeness, uniqueness, freshness, validity
    severity: str
    details: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
