import random
from typing import List, Dict
from app.learning.models import LearningSample


class SamplingEngine:
    @staticmethod
    def random_sample(samples: List[LearningSample], ratio: float = 0.2) -> List[LearningSample]:
        if not samples:
            return []
        k = max(1, int(len(samples) * ratio))
        return random.sample(samples, k)

    @staticmethod
    def hard_examples_sample(samples: List[LearningSample], max_confidence: float = 0.5) -> List[LearningSample]:
        """Returns samples that the model struggled with (low confidence or overridden by human)."""
        hard = [s for s in samples if s.confidence <= max_confidence or s.expected_output != s.corrected_output]
        return hard

    @staticmethod
    def balanced_sample(samples: List[LearningSample], max_per_class: int = 100) -> List[LearningSample]:
        """Balances the dataset across task_types to prevent class imbalance."""
        buckets: Dict[str, List[LearningSample]] = {}
        for s in samples:
            buckets.setdefault(s.task_type, []).append(s)
            
        balanced = []
        for task, items in buckets.items():
            if len(items) > max_per_class:
                balanced.extend(random.sample(items, max_per_class))
            else:
                balanced.extend(items)
                
        return balanced
