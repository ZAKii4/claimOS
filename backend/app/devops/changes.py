from typing import Dict, Any, List
import time


class ChangeManager:
    """Manages IT changes, Request for Comments (RFCs), and approvals."""

    _changes: List[Dict[str, Any]] = []

    @classmethod
    def propose_change(cls, title: str, risk_score: str) -> Dict[str, Any]:
        ch = {
            "id": f"rfc-{len(cls._changes)+1}",
            "title": title,
            "risk_score": risk_score,
            "status": "PENDING_APPROVAL",
            "date": time.time()
        }
        cls._changes.append(ch)
        return ch

    @classmethod
    def approve_change(cls, rfc_id: str) -> bool:
        for ch in cls._changes:
            if ch["id"] == rfc_id:
                ch["status"] = "APPROVED"
                return True
        return False

    @classmethod
    def get_changes(cls) -> List[Dict[str, Any]]:
        return cls._changes

    @classmethod
    def _reset(cls):
        cls._changes.clear()
