from typing import Dict, Any

class AIOpsEngine:
    """
    Basic anomaly detection and capacity forecasting.
    """
    def detect_anomalies(self, current_metrics: Dict[str, Any]) -> list:
        anomalies = []
        
        # Example: if latency is over 2.0s
        if current_metrics.get("avg_latency", 0) > 2.0:
            anomalies.append({
                "type": "latency_spike",
                "severity": "high",
                "message": "Average latency exceeded 2.0s threshold."
            })
            
        # Example: VRAM > 90%
        if current_metrics.get("vram_utilization", 0) > 90:
            anomalies.append({
                "type": "vram_exhaustion_warning",
                "severity": "medium",
                "message": "GPU VRAM usage is above 90%."
            })
            
        return anomalies
        
    def predict_capacity(self) -> Dict[str, Any]:
        """Simple linear mock projection for 30 days"""
        return {
            "days_until_db_full": 124,
            "gpu_saturation_trend": "increasing",
            "recommendation": "Provision additional GPU node next month."
        }

aiops_engine = AIOpsEngine()
