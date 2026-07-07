from typing import List, Dict, Any
from app.agentic_ai.core.registry import AgentRegistry


class SupervisorEngine:
    """Dynamically builds and orchestrates specialized agent teams."""

    @classmethod
    def build_team(cls, claim_context: Dict[str, Any]) -> List[str]:
        """Builds a team of agents based on the claim context."""
        team = ["OCRAgent", "ExtractionAgent"]
        
        fraud_score = claim_context.get("fraud_score", 0)
        if fraud_score > 50:
            team.append("FraudAgent")
            
        is_legal_complex = claim_context.get("legal_complexity", False)
        if is_legal_complex:
            team.append("LegalAgent")
            
        team.append("DecisionAgent")
        return team

    @classmethod
    def orchestrate(cls, claim_context: Dict[str, Any]) -> Dict[str, Any]:
        """Simulates the orchestration of the built team."""
        team = cls.build_team(claim_context)
        
        # Verify agents exist
        valid_team = []
        for name in team:
            if AgentRegistry.get_agent(name):
                valid_team.append(name)
                
        return {
            "status": "COMPLETED",
            "team_assembled": valid_team,
            "final_decision": "Approved" if claim_context.get("fraud_score", 0) < 50 else "Rejected"
        }
