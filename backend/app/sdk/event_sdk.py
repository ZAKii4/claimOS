from typing import Dict, Any, List
import time


class EventSDK:
    """Event bus SDK for plugins to publish/consume typed events."""

    _events: List[Dict[str, Any]] = []

    @classmethod
    def publish(cls, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        evt = {
            "type": event_type,
            "payload": payload,
            "timestamp": time.time()
        }
        cls._events.append(evt)
        return evt

    @classmethod
    def get_events(cls) -> List[Dict[str, Any]]:
        return cls._events

    @classmethod
    def _reset(cls):
        cls._events.clear()
