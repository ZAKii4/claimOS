from typing import Dict, Any, List
import time


class IncidentManager:
    """Manages system incidents, timelines, and resolution status."""

    _incidents: List[Dict[str, Any]] = []

    @classmethod
    def report_incident(cls, title: str, severity: str, impact: str) -> Dict[str, Any]:
        incident = {
            "id": f"inc-{len(cls._incidents)+1}",
            "title": title,
            "severity": severity,
            "impact": impact,
            "status": "OPEN",
            "timeline": [{"action": "REPORTED", "time": time.time()}]
        }
        cls._incidents.append(incident)
        return incident

    @classmethod
    def resolve_incident(cls, incident_id: str, root_cause: str) -> bool:
        for inc in cls._incidents:
            if inc["id"] == incident_id:
                inc["status"] = "RESOLVED"
                inc["root_cause"] = root_cause
                inc["timeline"].append({"action": "RESOLVED", "time": time.time()})
                return True
        return False

    @classmethod
    def get_incidents(cls) -> List[Dict[str, Any]]:
        return cls._incidents

    @classmethod
    def _reset(cls):
        cls._incidents.clear()
