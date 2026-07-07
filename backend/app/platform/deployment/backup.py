import hashlib
import json
import uuid
from typing import Dict, List, Optional, Any
from app.platform.tenant.models import BackupEntry


class BackupManager:
    """Backup & Disaster Recovery with integrity verification."""

    _backups: Dict[str, BackupEntry] = {}

    @classmethod
    def create_backup(cls, data: Dict[str, Any], tenant_id: str = "global", backup_type: str = "snapshot") -> BackupEntry:
        payload = json.dumps(data, sort_keys=True, default=str)
        checksum = hashlib.sha256(payload.encode()).hexdigest()

        entry = BackupEntry(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            backup_type=backup_type,
            data=data,
            checksum=checksum,
        )
        cls._backups[entry.id] = entry
        return entry

    @classmethod
    def restore(cls, backup_id: str) -> Optional[Dict[str, Any]]:
        entry = cls._backups.get(backup_id)
        if not entry:
            return None
        return entry.data

    @classmethod
    def verify_integrity(cls, backup_id: str) -> bool:
        entry = cls._backups.get(backup_id)
        if not entry:
            return False
        payload = json.dumps(entry.data, sort_keys=True, default=str)
        computed = hashlib.sha256(payload.encode()).hexdigest()
        return computed == entry.checksum

    @classmethod
    def get_backups(cls, tenant_id: str = None) -> List[BackupEntry]:
        if tenant_id:
            return [b for b in cls._backups.values() if b.tenant_id == tenant_id]
        return list(cls._backups.values())
