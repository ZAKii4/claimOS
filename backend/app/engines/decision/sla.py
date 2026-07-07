from typing import Tuple
from app.engines.decision.models import DecisionType, RiskLevel
from app.engines.decision.context import DecisionContext


class SLAEngine:
    """
    Calculates Priority (0-100) and SLA Deadline (in hours) based on risk and decision.
    """
    
    @staticmethod
    def calculate(decision: DecisionType, context: DecisionContext) -> Tuple[int, int]:
        priority = 0
        sla_hours = 48  # Default 48h
        
        # Risk modifiers
        if context.computed_risk_level == RiskLevel.CRITICAL:
            priority += 50
            sla_hours = 4
        elif context.computed_risk_level == RiskLevel.HIGH:
            priority += 30
            sla_hours = 24
            
        # Decision modifiers
        if decision == DecisionType.FRAUD_REVIEW:
            priority += 40
            sla_hours = min(sla_hours, 12)
        elif decision == DecisionType.HUMAN_REVIEW:
            priority += 10
            
        # Cap priority at 100
        priority = min(100, priority)
        
        return priority, sla_hours
