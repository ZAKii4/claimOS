from typing import List, Dict, Any
import time


class ActivityManager:
    """Manages the real-time activity feed for collaborative sessions."""

    _feed: List[Dict[str, Any]] = []

    @classmethod
    def emit_event(cls, user_id: str, room_id: str, action: str, details: str) -> Dict[str, Any]:
        """Records an event in the activity feed."""
        event = {
            "id": f"evt-{len(cls._feed) + 1}",
            "user_id": user_id,
            "room_id": room_id,
            "action": action,
            "details": details,
            "timestamp": time.time()
        }
        cls._feed.append(event)
        return event

    @classmethod
    def get_feed(cls, room_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves recent activities for a room."""
        room_events = [e for e in cls._feed if e["room_id"] == room_id]
        return sorted(room_events, key=lambda x: x["timestamp"], reverse=True)[:limit]

    @classmethod
    def _reset(cls):
        cls._feed.clear()
