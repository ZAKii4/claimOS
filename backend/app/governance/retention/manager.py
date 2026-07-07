from datetime import datetime, timedelta
from typing import Dict, List
from app.governance.models import RetentionPolicy, RetentionResult


class RetentionManager:
    """Document lifecycle management engine."""

    _policies: Dict[str, RetentionPolicy] = {}

    @classmethod
    def register_policy(cls, policy: RetentionPolicy):
        cls._policies[policy.document_type] = policy

    @classmethod
    def get_policies(cls) -> List[RetentionPolicy]:
        return list(cls._policies.values())

    @classmethod
    def compute_retention(
        cls,
        document_id: str,
        document_type: str,
        created_at: datetime = None,
    ) -> RetentionResult:
        """Compute expiration, archive, and deletion dates."""
        policy = cls._policies.get(document_type)
        if not policy:
            # Default: 5 years retention, 2 years archive
            policy = RetentionPolicy(document_type=document_type)

        base = created_at or datetime.utcnow()

        return RetentionResult(
            document_id=document_id,
            expiration_date=base + timedelta(days=policy.retention_days),
            archive_date=base + timedelta(days=policy.archive_after_days),
            deletion_date=base + timedelta(days=policy.retention_days + 90),  # 90 days grace
            legal_hold=policy.legal_hold,
        )
