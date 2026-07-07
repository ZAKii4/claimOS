from typing import Dict, Any, List
from app.analytics.lake.warehouse import AnalyticsWarehouse


class FraudAnalyticsEngine:
    """Analyzes fraud networks and typologies."""

    @classmethod
    def generate_fraud_heatmap(cls, tenant_id: str) -> Dict[str, float]:
        """Returns fraud rate by geographic region (dimension)."""
        facts = AnalyticsWarehouse.get_raw_facts(tenant_id, "fraud_alerts")
        
        region_counts = {}
        for f in facts:
            region = f.dimensions.get("region", "UNKNOWN")
            region_counts[region] = region_counts.get(region, 0) + 1
            
        total = sum(region_counts.values())
        if total == 0:
            return {}
            
        return {r: round((c / total) * 100, 2) for r, c in region_counts.items()}

    @classmethod
    def detect_fraud_network(cls, tenant_id: str) -> List[Dict[str, Any]]:
        """Simulates finding linked claims representing organized fraud."""
        facts = AnalyticsWarehouse.get_raw_facts(tenant_id, "fraud_alerts")
        
        # Simple simulation: group by similar IP or bank account dimension
        networks = {}
        for f in facts:
            bank = f.dimensions.get("bank_account")
            if bank:
                networks.setdefault(bank, []).append(f.id)
                
        # Return networks with > 1 claim
        return [{"bank_account": k, "claims": v} for k, v in networks.items() if len(v) > 1]
