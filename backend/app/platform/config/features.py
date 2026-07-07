import hashlib
from typing import Dict, List, Optional
from app.platform.tenant.models import FeatureFlag


class FeatureFlagEngine:
    """Feature flag evaluation with tenant, user, and percentage rollout support."""

    _flags: Dict[str, FeatureFlag] = {}

    @classmethod
    def register(cls, flag: FeatureFlag):
        cls._flags[flag.name] = flag

    @classmethod
    def get_all(cls) -> List[FeatureFlag]:
        return list(cls._flags.values())

    @classmethod
    def is_enabled(
        cls,
        flag_name: str,
        tenant_id: str = "",
        user_id: str = "",
    ) -> bool:
        flag = cls._flags.get(flag_name)
        if not flag:
            return False

        # User-level override (highest priority)
        if user_id and user_id in flag.user_overrides:
            return flag.user_overrides[user_id]

        # Tenant-level override
        if tenant_id and tenant_id in flag.tenant_overrides:
            return flag.tenant_overrides[tenant_id]

        # Global flag disabled
        if not flag.enabled:
            return False

        # Percentage rollout
        if flag.rollout_percentage < 100.0:
            # Deterministic hash-based bucketing
            bucket_key = f"{flag_name}:{tenant_id}:{user_id}"
            bucket = int(hashlib.md5(bucket_key.encode()).hexdigest(), 16) % 100
            return bucket < flag.rollout_percentage

        return True
