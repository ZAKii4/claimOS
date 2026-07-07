from typing import List, Dict, Any
from app.analytics.lake.warehouse import AnalyticsWarehouse
from datetime import datetime


class AdvancedAnalyticsEngine:
    """Calculates trends, seasonality, and anomalies using local logic."""

    @classmethod
    def detect_anomalies(cls, tenant_id: str, fact_type: str, measure: str) -> List[Dict[str, Any]]:
        """Simple statistical anomaly detection (Z-score based stub)."""
        facts = AnalyticsWarehouse.get_raw_facts(tenant_id, fact_type)
        if not facts:
            return []
            
        values = [f.measures.get(measure, 0.0) for f in facts if measure in f.measures]
        if not values:
            return []
            
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = variance ** 0.5
        
        anomalies = []
        for f in facts:
            val = f.measures.get(measure)
            if val is not None and std_dev > 0:
                z_score = abs(val - mean) / std_dev
                if z_score > 2.0:  # simplistic threshold
                    anomalies.append({
                        "fact_id": f.id,
                        "timestamp": f.timestamp.isoformat(),
                        "value": val,
                        "z_score": round(z_score, 2)
                    })
                    
        return anomalies

    @classmethod
    def analyze_trends(cls, tenant_id: str, fact_type: str, measure: str) -> Dict[str, Any]:
        """Simple trend direction analysis."""
        facts = AnalyticsWarehouse.get_raw_facts(tenant_id, fact_type)
        facts.sort(key=lambda x: x.timestamp)
        
        if len(facts) < 2:
            return {"trend": "neutral", "change_pct": 0.0}
            
        first_val = facts[0].measures.get(measure, 0.0)
        last_val = facts[-1].measures.get(measure, 0.0)
        
        if first_val == 0:
            change_pct = 100.0 if last_val > 0 else 0.0
        else:
            change_pct = ((last_val - first_val) / first_val) * 100
            
        trend = "up" if change_pct > 0 else "down" if change_pct < 0 else "neutral"
        
        return {
            "trend": trend,
            "change_pct": round(change_pct, 2)
        }
