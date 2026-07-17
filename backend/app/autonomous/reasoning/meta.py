from typing import Dict, Any, List


class MetaReasoningEngine:
    """Reflects on the system's own reasoning processes to improve strategies."""

    @classmethod
    def analyze_reasoning_trace(cls, trace: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes why a strategy succeeded or failed."""
        strategy = trace.get("strategy", "UNKNOWN")
        success = trace.get("success", False)
        
        insight = "Strategy effective." if success else "Strategy failed."
        adaptation = "Reinforce use of this strategy." if success else "Deprioritize this strategy."
        
        if not success and strategy == "Fast Path":
            adaptation = "Require human review for Fast Path on similar cases."
            
        return {
            "analyzed_strategy": strategy,
            "insight": insight,
            "adaptation_proposed": adaptation
        }
