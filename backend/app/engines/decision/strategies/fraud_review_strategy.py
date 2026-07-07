from app.engines.decision.base_strategy import BaseDecisionStrategy
from app.engines.decision.context import DecisionContext
from app.engines.decision.models import DecisionType


class FraudReviewStrategy(BaseDecisionStrategy):
    
    @property
    def name(self) -> str:
        return "FraudReviewStrategy"
        
    @property
    def priority(self) -> int:
        return 90  # High priority (run before Human or AutoApprove)
        
    def evaluate(self, context: DecisionContext) -> bool:
        alerts = context.validation_report.statistics.issues_by_category.get("FRAUD_HEURISTIC", 0)
        return alerts > context.policies.max_fraud_alerts_before_review
        
    def get_decision(self, context: DecisionContext) -> DecisionType:
        return DecisionType.FRAUD_REVIEW
        
    def get_reason(self) -> str:
        return "Fraud heuristics exceeded the permissible limit."
        
    def get_explanations(self, context: DecisionContext) -> list[str]:
        alerts = context.validation_report.statistics.issues_by_category.get("FRAUD_HEURISTIC", 0)
        limit = context.policies.max_fraud_alerts_before_review
        return [f"Detected {alerts} fraud alerts (limit is {limit}). Requires SIU (Special Investigation Unit) review."]
        
    def get_applied_rules(self) -> list[str]:
        return ["max_fraud_alerts_before_review"]
