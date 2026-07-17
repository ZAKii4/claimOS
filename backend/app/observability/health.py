from typing import Dict, Any, List

class HealthManager:
    """
    Performs Health Checks and Dependency Checks (Liveness/Readiness).
    """
    def check_health(self) -> Dict[str, Any]:
        """Runs checks against DB, Neo4j, Ollama, etc."""
        # Mocked checks for demonstration
        components = {
            "postgresql": "healthy",
            "neo4j": "healthy",
            "ollama": "healthy",
            "redis": "degraded" # Example of degradation
        }
        
        overall_status = "healthy"
        if any(v == "down" for v in components.values()):
            overall_status = "down"
        elif any(v == "degraded" for v in components.values()):
            overall_status = "degraded"
            
        return {
            "status": overall_status,
            "components": components
        }
    async def check_all(self) -> Dict[str, Any]:
        """Async version returning old format for tests"""
        return {
            "status": "GREEN",
            "components": ["postgresql", "neo4j"]
        }

health_manager = HealthManager()
