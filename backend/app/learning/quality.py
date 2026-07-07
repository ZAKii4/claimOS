from typing import List, Dict
from app.learning.models import LearningSample, DatasetQualityReport

class QualityEngine:
    def evaluate(self, dataset_id: str, samples: List[LearningSample]) -> DatasetQualityReport:
        total = len(samples)
        if total == 0:
            return DatasetQualityReport(
                dataset_id=dataset_id,
                total_samples=0,
                class_distribution={},
                avg_confidence=0.0,
                invalid_samples=0,
                review_coverage_percent=0.0
            )

        class_dist: Dict[str, int] = {}
        total_conf = 0.0
        invalid = 0
        
        for sample in samples:
            # Task specific distribution
            task = sample.task_type
            class_dist[task] = class_dist.get(task, 0) + 1
            
            total_conf += sample.confidence
            
            # Simple invalid check (empty inputs/outputs)
            if not sample.input_data or not sample.corrected_output:
                invalid += 1

        avg_conf = total_conf / total
        
        return DatasetQualityReport(
            dataset_id=dataset_id,
            total_samples=total,
            class_distribution=class_dist,
            avg_confidence=avg_conf,
            invalid_samples=invalid,
            review_coverage_percent=100.0 # MVP assumption
        )
