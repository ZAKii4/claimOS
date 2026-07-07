from typing import Optional, Any
from pydantic import BaseModel

from app.engines.evidence_graph.models import EvidenceGraphResult
from app.engines.validation.report import ValidationReport
from app.engines.decision.policy import BusinessPolicies
from app.engines.decision.models import RiskLevel


class DecisionContext(BaseModel):
    """
    Context passed to all Decision Strategies and ancillary engines.
    """
    claim_id: str
    evidence_graph: EvidenceGraphResult
    validation_report: ValidationReport
    policies: BusinessPolicies = BusinessPolicies()
    
    # Optional Risk Indicators computed on the fly
    computed_risk_level: Optional[RiskLevel] = None
    
    # Historical context or external signals (simulated for MVP)
    history_signals: dict[str, Any] = {}
