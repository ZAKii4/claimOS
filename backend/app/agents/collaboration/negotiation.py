from typing import List, Dict, Any
from enum import Enum


class NegotiationStrategy(str, Enum):
    MAJORITY_VOTING = "MAJORITY_VOTING"
    WEIGHTED_CONFIDENCE = "WEIGHTED_CONFIDENCE"
    EXPERT_PRIORITY = "EXPERT_PRIORITY"
    HUMAN_ESCALATION = "HUMAN_ESCALATION"


class AgentProposal:
    def __init__(self, agent_id: str, decision: str, confidence: float, weight: float = 1.0):
        self.agent_id = agent_id
        self.decision = decision
        self.confidence = confidence
        self.weight = weight


class NegotiationEngine:
    """Resolves conflicts between multiple agent proposals."""

    @classmethod
    def resolve(
        cls, 
        tenant_id: str, 
        proposals: List[AgentProposal], 
        strategy: NegotiationStrategy = NegotiationStrategy.WEIGHTED_CONFIDENCE
    ) -> Dict[str, Any]:
        """Runs the negotiation to reach a consensus."""
        
        if not proposals:
            return {"consensus": "NONE", "strategy": strategy, "confidence": 0.0}

        if strategy == NegotiationStrategy.MAJORITY_VOTING:
            votes = {}
            for p in proposals:
                votes[p.decision] = votes.get(p.decision, 0) + 1
            
            # Find max
            winner = max(votes.items(), key=lambda x: x[1])
            return {
                "consensus": winner[0],
                "strategy": strategy,
                "confidence": winner[1] / len(proposals)
            }
            
        elif strategy == NegotiationStrategy.WEIGHTED_CONFIDENCE:
            scores = {}
            for p in proposals:
                scores[p.decision] = scores.get(p.decision, 0.0) + (p.confidence * p.weight)
                
            winner = max(scores.items(), key=lambda x: x[1])
            # normalize approx confidence
            total_score = sum(scores.values())
            conf = winner[1] / total_score if total_score > 0 else 0.0
            
            return {
                "consensus": winner[0],
                "strategy": strategy,
                "confidence": round(conf, 2)
            }
            
        elif strategy == NegotiationStrategy.HUMAN_ESCALATION:
            return {
                "consensus": "ESCALATED_TO_HUMAN",
                "strategy": strategy,
                "confidence": 0.0
            }

        return {"consensus": proposals[0].decision, "strategy": strategy, "confidence": proposals[0].confidence}
