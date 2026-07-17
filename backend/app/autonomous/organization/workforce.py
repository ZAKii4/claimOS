from typing import Dict, Any
from app.autonomous.organization.teams import AIOrganizationEngine


class WorkforceManager:
    """Autonomously scales and distributes the AI workforce based on load."""

    @classmethod
    def analyze_and_scale(cls, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes system load and scales teams automatically."""
        
        cpu_load = metrics.get("cpu_load", 0)
        pending_tasks = metrics.get("pending_tasks", 0)
        
        action_taken = "NO_ACTION"
        new_team = None
        
        if pending_tasks > 1000 and cpu_load < 80:
            action_taken = "CREATE_TEAM"
            new_team = AIOrganizationEngine.create_team(
                name="Overflow processing team",
                manager="AutoManager",
                agents=["Agent1", "Agent2"]
            )
        elif pending_tasks < 50:
            action_taken = "SCALE_DOWN"
            
        return {
            "status": "SCALED",
            "action_taken": action_taken,
            "new_team_id": new_team.id if new_team else None
        }
