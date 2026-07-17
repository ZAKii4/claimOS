from typing import Dict, Any


class TeamAnalyticsEngine:
    """Generates collaborative performance KPIs."""

    @classmethod
    def compute_team_metrics(cls, room_activities: list) -> Dict[str, Any]:
        if not room_activities:
            return {
                "avg_resolution_time": 0,
                "total_validations": 0,
                "total_corrections": 0,
                "team_performance": 0.0
            }
            
        validations = sum(1 for e in room_activities if e.get("action") == "validate")
        corrections = sum(1 for e in room_activities if e.get("action") == "correct")
        
        perf = (validations / (validations + corrections)) if (validations + corrections) > 0 else 1.0
        
        return {
            "avg_resolution_time": 120.5, # Mock value
            "total_validations": validations,
            "total_corrections": corrections,
            "team_performance": round(perf, 2)
        }
