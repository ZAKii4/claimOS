from typing import Dict, Any, List
import uuid


class DatasetGovernanceManager:
    """Manages Dataset versioning and bias/drift calculations."""

    _datasets: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register_dataset(cls, name: str, version: str) -> Dict[str, Any]:
        d_id = str(uuid.uuid4())
        dataset = {
            "id": d_id,
            "name": name,
            "version": version,
            "completeness": 0.99,
            "freshness": "1 day ago",
            "bias_score": 0.05,
            "drift_score": 0.01
        }
        cls._datasets[d_id] = dataset
        return dataset

    @classmethod
    def get_all(cls) -> List[Dict[str, Any]]:
        return list(cls._datasets.values())

    @classmethod
    def _reset(cls):
        cls._datasets.clear()
