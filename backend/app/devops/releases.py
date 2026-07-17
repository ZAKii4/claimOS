from typing import Dict, Any, List
import time


class ReleaseManager:
    """Manages semantic versioning, release notes, and history."""

    _releases: List[Dict[str, Any]] = []

    @classmethod
    def create_release(cls, version: str, author: str, checksum: str) -> Dict[str, Any]:
        release = {
            "version": version,
            "author": author,
            "date": time.time(),
            "checksum": checksum,
            "status": "CREATED"
        }
        cls._releases.append(release)
        return release

    @classmethod
    def get_releases(cls) -> List[Dict[str, Any]]:
        return sorted(cls._releases, key=lambda x: x["version"], reverse=True)

    @classmethod
    def _reset(cls):
        cls._releases.clear()
