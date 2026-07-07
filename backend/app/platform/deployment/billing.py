from typing import Dict, List
from app.platform.tenant.models import TenantUsage


class BillingEngine:
    """Cost allocation engine per tenant."""

    _usage: Dict[str, TenantUsage] = {}

    # Cost per unit
    OCR_COST = 0.02
    LLM_COST = 0.05
    STORAGE_COST_PER_MB = 0.001
    CLAIM_COST = 0.10

    @classmethod
    def record_ocr(cls, tenant_id: str, count: int = 1):
        cls._ensure(tenant_id)
        cls._usage[tenant_id].ocr_calls += count
        cls._recalculate(tenant_id)

    @classmethod
    def record_llm(cls, tenant_id: str, count: int = 1):
        cls._ensure(tenant_id)
        cls._usage[tenant_id].llm_calls += count
        cls._recalculate(tenant_id)

    @classmethod
    def record_storage(cls, tenant_id: str, mb: float):
        cls._ensure(tenant_id)
        cls._usage[tenant_id].storage_mb += mb
        cls._recalculate(tenant_id)

    @classmethod
    def record_claim(cls, tenant_id: str, count: int = 1):
        cls._ensure(tenant_id)
        cls._usage[tenant_id].claims_processed += count
        cls._recalculate(tenant_id)

    @classmethod
    def get_usage(cls, tenant_id: str) -> TenantUsage:
        cls._ensure(tenant_id)
        return cls._usage[tenant_id]

    @classmethod
    def get_all_usage(cls) -> List[TenantUsage]:
        return list(cls._usage.values())

    @classmethod
    def _ensure(cls, tenant_id: str):
        if tenant_id not in cls._usage:
            cls._usage[tenant_id] = TenantUsage(tenant_id=tenant_id)

    @classmethod
    def _recalculate(cls, tenant_id: str):
        u = cls._usage[tenant_id]
        u.total_cost = round(
            u.ocr_calls * cls.OCR_COST +
            u.llm_calls * cls.LLM_COST +
            u.storage_mb * cls.STORAGE_COST_PER_MB +
            u.claims_processed * cls.CLAIM_COST, 4
        )
