from typing import List, Dict, Any
from app.learning.models import LearningSample, DatasetMetadata
from app.learning.feedback_collector import FeedbackCollector
from app.learning.dataset_builder import DatasetBuilder
from app.learning.dataset_versioning import DatasetVersioning
from app.learning.export import ExportEngine
from app.learning.sampling import SamplingEngine


class LearningManager:
    """Orchestrator for the Continuous Learning Platform (MLOps)."""
    
    def __init__(self):
        self.collector = FeedbackCollector()
        self.builder = DatasetBuilder()
        self.versioning = DatasetVersioning()
        self.exporter = ExportEngine()
        self.sampler = SamplingEngine()
        
    def process_review_session(self, session_data: dict, audit_logs: List[dict]) -> List[LearningSample]:
        """Ingest a review session and extract learning samples."""
        samples = self.collector.extract_from_audit(session_data, audit_logs)
        return samples
        
    def build_and_export_datasets(self, samples: List[LearningSample]) -> Dict[str, DatasetMetadata]:
        """Takes a pool of samples, segments them, versions them, and exports them."""
        segmented = self.builder.segment_by_task(samples)
        
        results = {}
        for task_type, task_samples in segmented.items():
            # Apply sampling if necessary (e.g. balance)
            final_samples = self.sampler.balanced_sample(task_samples, max_per_class=10000)
            
            # Versioning
            dataset_id = f"dataset_{task_type.lower()}"
            metadata = self.versioning.create_version(dataset_id, task_type, final_samples)
            
            # Export
            self.exporter.export_jsonl(f"{dataset_id}_{metadata.version}", final_samples)
            
            results[task_type] = metadata
            
        return results
