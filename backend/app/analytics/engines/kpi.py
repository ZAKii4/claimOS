from typing import Dict
from app.analytics.lake.warehouse import AnalyticsWarehouse


class KPIEngine:
    """Calculates various KPIs (Business, Ops, AI, Infra)."""

    @classmethod
    def calculate_automation_rate(cls, tenant_id: str) -> float:
        agg = AnalyticsWarehouse.query_aggregate(tenant_id, "claims")
        total = agg.get("total_claims", 0.0)
        automated = agg.get("automated_claims", 0.0)
        if total == 0:
            return 0.0
        return round((automated / total) * 100, 2)

    @classmethod
    def calculate_average_processing_time(cls, tenant_id: str) -> float:
        agg = AnalyticsWarehouse.query_aggregate(tenant_id, "claims")
        total = agg.get("total_claims", 0.0)
        total_time = agg.get("total_processing_time_sec", 0.0)
        if total == 0:
            return 0.0
        return round(total_time / total, 2)

    @classmethod
    def calculate_ocr_accuracy(cls, tenant_id: str) -> float:
        agg = AnalyticsWarehouse.query_aggregate(tenant_id, "ocr")
        total = agg.get("total_fields", 0.0)
        correct = agg.get("correct_fields", 0.0)
        if total == 0:
            return 0.0
        return round((correct / total) * 100, 2)

    @classmethod
    def calculate_fraud_rate(cls, tenant_id: str) -> float:
        agg = AnalyticsWarehouse.query_aggregate(tenant_id, "fraud_alerts")
        total_claims = AnalyticsWarehouse.query_aggregate(tenant_id, "claims").get("total_claims", 0.0)
        total_frauds = agg.get("confirmed_frauds", 0.0)
        
        if total_claims == 0:
            return 0.0
        return round((total_frauds / total_claims) * 100, 2)
