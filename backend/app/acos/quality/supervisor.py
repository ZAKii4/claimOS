from typing import Dict, Any


class QualitySupervisor:
    """Continuously monitors outputs for hallucinations, grounding, and compliance."""

    @classmethod
    def audit_output(cls, output_text: str, source_context: str) -> Dict[str, Any]:
        """Simulates quality auditing."""
        
        # Simple heuristic for testing: if output mentions "unverified", flag it
        is_hallucinated = "unverified" in output_text.lower()
        is_grounded = "source" in output_text.lower() and not is_hallucinated
        
        score = 1.0
        if is_hallucinated:
            score -= 0.5
        if not is_grounded:
            score -= 0.3
            
        penalty_applied = score <= 0.7
        
        return {
            "is_hallucinated": is_hallucinated,
            "is_grounded": is_grounded,
            "quality_score": round(score, 2),
            "penalty_applied": penalty_applied,
            "action": "PENALIZE" if penalty_applied else "PASS"
        }
