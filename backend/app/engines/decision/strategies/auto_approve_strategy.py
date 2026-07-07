from app.engines.decision.base_strategy import BaseDecisionStrategy
from app.engines.decision.context import DecisionContext
from app.engines.decision.models import DecisionType


class AutoApproveStrategy(BaseDecisionStrategy):
    
    @property
    def name(self) -> str:
        return "AutoApproveStrategy"
        
    @property
    def priority(self) -> int:
        return 10  # Low priority, runs if no higher priority issues exist
        
    def evaluate(self, context: DecisionContext) -> bool:
        summary = context.validation_report.summary
        if summary.has_blockers or summary.has_criticals:
            return False
            
        if not context.policies.allow_auto_approve_with_warnings and not summary.is_valid:
            return False
            
        return summary.global_score >= context.policies.min_validation_score_for_auto_approve
        
    def get_decision(self, context: DecisionContext) -> DecisionType:
        return DecisionType.AUTO_APPROVED
        
    def get_reason(self) -> str:
        return "Claim fully validated with high confidence score."
        
    def get_explanations(self, context: DecisionContext) -> list[str]:
        score = context.validation_report.summary.global_score * 100
        return [
            f"Validation Score ({score:.1f}%) exceeds the auto-approval threshold.",
            "No Critical or Blocker issues were detected."
        ]
        
    def get_applied_rules(self) -> list[str]:
        return ["min_validation_score_for_auto_approve", "allow_auto_approve_with_warnings"]
