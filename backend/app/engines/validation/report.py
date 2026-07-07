import uuid
from typing import Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

from app.engines.validation.severity import ValidationSeverity


class ValidationIssue(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str
    rule_name: str
    category: str
    severity: ValidationSeverity
    message: str
    explanation: str
    target_node_id: Optional[str] = None
    target_edge_id: Optional[str] = None
    suggested_correction: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationStatistics(BaseModel):
    total_rules_evaluated: int = 0
    total_issues_found: int = 0
    issues_by_severity: dict[str, int] = Field(default_factory=dict)
    issues_by_category: dict[str, int] = Field(default_factory=dict)


class ValidationSummary(BaseModel):
    is_valid: bool
    global_score: float = Field(..., ge=0.0, le=1.0)
    has_blockers: bool
    has_criticals: bool


class ValidationReport(BaseModel):
    claim_id: str
    summary: ValidationSummary
    statistics: ValidationStatistics
    issues: list[ValidationIssue] = Field(default_factory=list)
    execution_time_ms: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
