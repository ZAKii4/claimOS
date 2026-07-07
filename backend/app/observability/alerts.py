import uuid
from typing import List
from app.observability.models import Alert, AlertSeverity


class AlertEngine:
    """Rule-based alert generator."""
    
    _alerts: List[Alert] = []
    
    @classmethod
    def check_cpu(cls, cpu_usage: float):
        if cpu_usage > 95.0:
            cls.raise_alert(
                category="Infrastructure",
                severity=AlertSeverity.CRITICAL,
                message=f"CPU Spike detected: {cpu_usage}%",
                recommended_action="Scale out workers"
            )
            
    @classmethod
    def check_latency(cls, endpoint: str, latency_ms: float):
        if latency_ms > 5000:
            cls.raise_alert(
                category="Performance",
                severity=AlertSeverity.WARNING,
                message=f"High latency on {endpoint}: {latency_ms}ms",
                recommended_action="Investigate bottlenecks"
            )
            
    @classmethod
    def raise_alert(cls, category: str, severity: AlertSeverity, message: str, recommended_action: str):
        alert = Alert(
            id=str(uuid.uuid4()),
            category=category,
            severity=severity,
            message=message,
            recommended_action=recommended_action
        )
        cls._alerts.append(alert)
        
    @classmethod
    def get_alerts(cls) -> List[Alert]:
        return sorted(cls._alerts, key=lambda x: x.timestamp, reverse=True)
