from typing import List, Dict, Any
from app.analytics.engines.kpi import KPIEngine


class DashboardEngine:
    """Generates dynamic dashboard definitions and widget data."""

    @classmethod
    def get_executive_dashboard(cls, tenant_id: str) -> Dict[str, Any]:
        """Returns layout and data for the executive dashboard."""
        
        automation = KPIEngine.calculate_automation_rate(tenant_id)
        avg_time = KPIEngine.calculate_average_processing_time(tenant_id)
        fraud = KPIEngine.calculate_fraud_rate(tenant_id)
        
        return {
            "title": "Executive Dashboard",
            "widgets": [
                {
                    "type": "KPI_CARD",
                    "title": "Automation Rate",
                    "value": f"{automation}%"
                },
                {
                    "type": "KPI_CARD",
                    "title": "Avg Processing Time",
                    "value": f"{avg_time}s"
                },
                {
                    "type": "KPI_CARD",
                    "title": "Fraud Rate",
                    "value": f"{fraud}%"
                },
                {
                    "type": "TIME_SERIES",
                    "title": "Claim Volume over 7 days",
                    "data": [10, 15, 12, 20, 25, 22, 30]  # Stub
                }
            ]
        }
