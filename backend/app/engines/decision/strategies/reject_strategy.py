from app.engines.decision.base_strategy import BaseDecisionStrategy
from app.engines.decision.context import DecisionContext
from app.engines.decision.models import DecisionType


class RejectStrategy(BaseDecisionStrategy):
    
    @property
    def name(self) -> str:
        return "RejectStrategy"
        
    @property
    def priority(self) -> int:
        return 100  # Highest priority
        
    def evaluate(self, context: DecisionContext) -> bool:
        if context.policies.reject_on_blocker:
            return context.validation_report.summary.has_blockers
        return False
        
    def get_decision(self, context: DecisionContext) -> DecisionType:
        return DecisionType.AUTO_REJECTED
        
    def get_reason(self) -> str:
        return "Validation BLOCKER issues found."
        
    def get_explanations(self, context: DecisionContext) -> list[str]:
        blockers = [i for i in context.validation_report.issues if i.severity.name == "BLOCKER"]
        explanations = ["Claim cannot proceed due to critical blockers:"]
        for b in blockers:
            explanations.append(f"- {b.message}")
        return explanations
        
    def get_applied_rules(self) -> list[str]:
        return ["reject_on_blocker"]
