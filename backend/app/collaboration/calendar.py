from typing import Dict, List, Any
import uuid


class CalendarManager:
    """Manages enterprise calendar, SLAs, and deadlines."""

    _events: List[Dict[str, Any]] = []

    @classmethod
    def create_event(cls, title: str, timestamp: float, event_type: str = "meeting") -> Dict[str, Any]:
        evt = {
            "id": str(uuid.uuid4()),
            "title": title,
            "timestamp": timestamp,
            "type": event_type
        }
        cls._events.append(evt)
        return evt

    @classmethod
    def get_events(cls) -> List[Dict[str, Any]]:
        return sorted(cls._events, key=lambda e: e["timestamp"])

    @classmethod
    def _reset(cls):
        cls._events.clear()
