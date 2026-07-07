from typing import Optional
from app.engines.decision.models import DecisionType, QueueName
from app.engines.decision.context import DecisionContext


class RoutingEngine:
    """
    Determines which queue a claim should be routed to, based on the decision
    and the context.
    """
    
    @staticmethod
    def route(decision: DecisionType, context: DecisionContext) -> Optional[QueueName]:
        if decision == DecisionType.AUTO_APPROVED:
            return QueueName.AUTO_PROCESSING
            
        if decision == DecisionType.AUTO_REJECTED:
            return QueueName.AUTO_PROCESSING
            
        if decision == DecisionType.FRAUD_REVIEW:
            return QueueName.FRAUD
            
        if decision == DecisionType.HUMAN_REVIEW:
            # Check if it needs a specific expert based on validation issues
            # E.g., if there's a specific issue in the Medical category
            medical_issues = context.validation_report.statistics.issues_by_category.get("MEDICAL", 0)
            if medical_issues > 0:
                return QueueName.MEDICAL_EXPERT
                
            return QueueName.HUMAN_REVIEW
            
        if decision == DecisionType.REQUEST_MORE_DOCUMENTS:
            return QueueName.CUSTOMER_SERVICE
            
        return None
