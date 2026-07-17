from typing import Dict, Any, List
import time


class BackupManager:
    """Manages system backups, snapshots, and restore procedures."""

    _backups: List[Dict[str, Any]] = []

    @classmethod
    def create_backup(cls, b_type: str = "FULL") -> Dict[str, Any]:
        bkp = {
            "id": f"bkp-{len(cls._backups)+1}",
            "type": b_type,
            "timestamp": time.time(),
            "status": "COMPLETED",
            "size": "14GB"
        }
        cls._backups.append(bkp)
        return bkp

    @classmethod
    def restore(cls, backup_id: str) -> bool:
        for b in cls._backups:
            if b["id"] == backup_id:
                return True
        return False

    @classmethod
    def get_backups(cls) -> List[Dict[str, Any]]:
        return cls._backups

    @classmethod
    def _reset(cls):
        cls._backups.clear()
