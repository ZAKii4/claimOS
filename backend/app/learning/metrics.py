from typing import List
from app.learning.models import LearningSample


class MetricsEngine:
    
    @staticmethod
    def calculate_automation_rate(total_claims: int, auto_approved: int) -> float:
        if total_claims == 0:
            return 0.0
        return (auto_approved / total_claims) * 100.0
        
    @staticmethod
    def calculate_override_rate(samples: List[LearningSample]) -> float:
        """Percentage of samples where human corrected the expected output."""
        if not samples:
            return 0.0
            
        overridden = sum(1 for s in samples if s.expected_output != s.corrected_output)
        return (overridden / len(samples)) * 100.0
        
    @staticmethod
    def calculate_f1_score(true_positives: int, false_positives: int, false_negatives: int) -> float:
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        
        if precision + recall == 0:
            return 0.0
            
        return 2 * (precision * recall) / (precision + recall)
