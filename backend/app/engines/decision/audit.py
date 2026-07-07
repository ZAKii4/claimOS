import uuid
from app.engines.decision.models import DecisionAuditEntry, DecisionType


class AuditLogger:
    """
    Generates Audit Trail entries for decisions made.
    """
    
    @staticmethod
    def log_decision(
        strategy_name: str,
        decision: DecisionType,
        reason: str,
        policy_version: str,
        applied_rules: list[str]
    ) -> DecisionAuditEntry:
        return DecisionAuditEntry(
            id=str(uuid.uuid4()),
            strategy_used=strategy_name,
            rules_applied=applied_rules,
            reason=reason,
            decision=decision,
            policy_version=policy_version
        )
