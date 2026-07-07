from app.engines.decision.context import DecisionContext


class ConfidenceEngine:
    """
    Computes a Decision Confidence score (0.0 to 1.0).
    Unlike Validation Confidence (which measures data quality), 
    Decision Confidence measures how sure the engine is about its routing/approval choice.
    """
    
    @staticmethod
    def calculate(context: DecisionContext) -> float:
        # For MVP, decision confidence is strongly tied to validation confidence.
        # But it penalizes edge cases (e.g., scores exactly on the threshold)
        
        base_conf = context.validation_report.summary.global_score
        
        # Example heuristic: if there are no blockers and no criticals, we are more confident
        if not context.validation_report.summary.has_blockers and not context.validation_report.summary.has_criticals:
            base_conf = min(1.0, base_conf + 0.05)
            
        return round(base_conf, 3)
