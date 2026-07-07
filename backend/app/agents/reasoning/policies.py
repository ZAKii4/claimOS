from enum import Enum
from typing import Dict, Any, List


class AutonomyLevel(str, Enum):
    MANUAL = "MANUAL"
    ASSISTED = "ASSISTED"
    SUPERVISED = "SUPERVISED"
    AUTONOMOUS = "AUTONOMOUS"


class ExecutionPolicyManager:
    """Manages autonomy levels per tenant."""

    _tenant_policies: Dict[str, AutonomyLevel] = {}

    @classmethod
    def set_level(cls, tenant_id: str, level: AutonomyLevel):
        cls._tenant_policies[tenant_id] = level

    @classmethod
    def get_level(cls, tenant_id: str) -> AutonomyLevel:
        return cls._tenant_policies.get(tenant_id, AutonomyLevel.ASSISTED)

    @classmethod
    def can_execute_autonomously(cls, tenant_id: str) -> bool:
        return cls.get_level(tenant_id) == AutonomyLevel.AUTONOMOUS

    @classmethod
    def requires_human_supervision(cls, tenant_id: str) -> bool:
        return cls.get_level(tenant_id) in [AutonomyLevel.SUPERVISED, AutonomyLevel.MANUAL]
