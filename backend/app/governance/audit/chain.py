import hashlib
import json
import uuid
from typing import List, Dict, Any
from app.governance.models import AuditEntry


class AuditChain:
    """
    Tamper-proof audit log.
    Each entry contains the SHA-256 hash of the previous entry,
    creating an unforgeable chain (blockchain-like).
    """

    _entries: List[AuditEntry] = []

    @classmethod
    def record(cls, actor: str, action: str, resource: str = "", details: Dict[str, Any] = None) -> AuditEntry:
        """Record a new audit event and chain it to the previous entry."""
        prev_hash = cls._entries[-1].entry_hash if cls._entries else "GENESIS"

        entry = AuditEntry(
            id=str(uuid.uuid4()),
            actor=actor,
            action=action,
            resource=resource,
            details=details or {},
            prev_hash=prev_hash,
        )
        # Compute hash of this entry
        payload = json.dumps({
            "id": entry.id,
            "actor": entry.actor,
            "action": entry.action,
            "resource": entry.resource,
            "prev_hash": entry.prev_hash,
        }, sort_keys=True)
        entry.entry_hash = hashlib.sha256(payload.encode()).hexdigest()

        cls._entries.append(entry)
        return entry

    @classmethod
    def verify_chain(cls) -> bool:
        """Verify the integrity of the entire audit chain."""
        if not cls._entries:
            return True

        for i, entry in enumerate(cls._entries):
            # Check prev_hash linkage
            expected_prev = cls._entries[i - 1].entry_hash if i > 0 else "GENESIS"
            if entry.prev_hash != expected_prev:
                return False

            # Recompute and verify hash
            payload = json.dumps({
                "id": entry.id,
                "actor": entry.actor,
                "action": entry.action,
                "resource": entry.resource,
                "prev_hash": entry.prev_hash,
            }, sort_keys=True)
            computed = hashlib.sha256(payload.encode()).hexdigest()
            if computed != entry.entry_hash:
                return False

        return True

    @classmethod
    def get_entries(cls) -> List[AuditEntry]:
        return list(cls._entries)
