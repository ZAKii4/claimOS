from app.engines.decision.models import RiskLevel
from app.engines.decision.context import DecisionContext


class RiskEngine:
    """
    Evaluates the overall risk of a claim based on validations, fraud alerts, 
    and historical signals.
    """
    
    @staticmethod
    def evaluate(context: DecisionContext) -> RiskLevel:
        report = context.validation_report
        stats = report.statistics
        
        # 1. Critical Risk
        # - Has Blockers or Validation Score is severely low
        # - Or has high fraud alerts
        fraud_alerts = stats.issues_by_category.get("FRAUD_HEURISTIC", 0)
        
        if report.summary.has_blockers or fraud_alerts > context.policies.max_fraud_alerts_before_review:
            return RiskLevel.CRITICAL
            
        # 2. High Risk
        # - Has Criticals or Score < 0.70
        if report.summary.has_criticals or report.summary.global_score < context.policies.human_review_threshold:
            return RiskLevel.HIGH
            
        # 3. Medium Risk
        # - Has Warnings or Score between 0.70 and 0.95
        if not report.summary.is_valid or report.summary.global_score < context.policies.min_validation_score_for_auto_approve:
            return RiskLevel.MEDIUM
            
        # 4. Low Risk
        return RiskLevel.LOW
