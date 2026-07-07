from typing import Dict, List, Optional
from app.governance.models import Policy, PolicyRule, PolicyDecision
from app.workflows.expressions import ExpressionEngine


class PolicyEngine:
    """Versioned policy evaluation engine."""

    _policies: Dict[str, Policy] = {}

    @classmethod
    def register_policy(cls, policy: Policy):
        cls._policies[policy.id] = policy

    @classmethod
    def get_all_policies(cls) -> List[Policy]:
        return list(cls._policies.values())

    @classmethod
    def evaluate(cls, policy_id: str, context: Dict) -> PolicyDecision:
        """Evaluate all rules of a policy against a context. First matching rule wins."""
        policy = cls._policies.get(policy_id)
        if not policy or not policy.active:
            return PolicyDecision.ALLOW

        for rule in policy.rules:
            try:
                if ExpressionEngine.evaluate(rule.condition, context):
                    return rule.decision
            except Exception:
                continue

        return PolicyDecision.ALLOW  # Default if no rule matches
