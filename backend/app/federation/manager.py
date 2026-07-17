from typing import Dict, Any, List

class FederationManager:
    """Manages cross-cluster topology and trust levels."""

    _clusters: Dict[str, Dict[str, Any]] = {
        "cluster-eu-west": {"region": "France", "trust": "HIGH", "status": "ONLINE"},
        "cluster-eu-central": {"region": "Germany", "trust": "HIGH", "status": "ONLINE"},
        "cluster-af-north": {"region": "Morocco", "trust": "HIGH", "status": "ONLINE"}
    }

    @classmethod
    def join_federation(cls, cluster_id: str, region: str) -> Dict[str, Any]:
        cls._clusters[cluster_id] = {"region": region, "trust": "PENDING", "status": "ONLINE"}
        return {"id": cluster_id, "status": "JOINED"}

    @classmethod
    def get_clusters(cls) -> List[Dict[str, Any]]:
        return [{"id": k, **v} for k, v in cls._clusters.items()]

    @classmethod
    def get_regions(cls) -> List[str]:
        return list(set(v["region"] for v in cls._clusters.values()))

    @classmethod
    def _reset(cls):
        cls._clusters = {
            "cluster-eu-west": {"region": "France", "trust": "HIGH", "status": "ONLINE"},
            "cluster-eu-central": {"region": "Germany", "trust": "HIGH", "status": "ONLINE"},
            "cluster-af-north": {"region": "Morocco", "trust": "HIGH", "status": "ONLINE"}
        }
