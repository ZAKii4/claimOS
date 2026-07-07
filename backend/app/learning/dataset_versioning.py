import hashlib
import json
from typing import List, Dict
from datetime import datetime
from app.learning.models import DatasetMetadata, LearningSample


class DatasetVersioning:
    @staticmethod
    def _compute_hash(samples: List[LearningSample]) -> str:
        """Compute a deterministic hash for a given set of samples."""
        # Sort by ID to ensure deterministic order
        sorted_samples = sorted(samples, key=lambda s: s.id)
        
        hasher = hashlib.sha256()
        for sample in sorted_samples:
            # We hash the essential content that defines the sample
            content = f"{sample.id}-{json.dumps(sample.corrected_output, sort_keys=True)}"
            hasher.update(content.encode('utf-8'))
            
        return hasher.hexdigest()

    def create_version(self, dataset_id: str, task_type: str, samples: List[LearningSample], previous_version: str = "v1.0.0") -> DatasetMetadata:
        """
        Creates a new immutable version metadata for the dataset.
        In a real scenario, version incrementing would parse previous_version (e.g. v1.0.1).
        """
        signature = self._compute_hash(samples)
        
        # Simple bump for MVP
        major, minor, patch = previous_version.lstrip('v').split('.')
        new_version = f"v{major}.{minor}.{int(patch) + 1}"
        
        source_reviews = list(set([s.review_id for s in samples]))
        
        return DatasetMetadata(
            dataset_id=dataset_id,
            version=new_version,
            task_type=task_type,
            hash_signature=signature,
            creation_date=datetime.utcnow(),
            statistics={"total_samples": len(samples)},
            source_reviews=source_reviews
        )
