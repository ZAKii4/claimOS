from typing import List, Dict
from collections import defaultdict
from app.observability.models import TimelineEvent


class TimelineEngine:
    """Chronological event aggregator per claim."""
    
    _timelines: Dict[str, List[TimelineEvent]] = defaultdict(list)
    
    @classmethod
    def record_event(cls, claim_id: str, event_type: str, actor: str, payload: dict = None, duration_ms: float = None):
        event = TimelineEvent(
            claim_id=claim_id,
            event_type=event_type,
            actor=actor,
            duration_ms=duration_ms,
            payload=payload or {}
        )
        cls._timelines[claim_id].append(event)
        
    @classmethod
    def get_timeline(cls, claim_id: str) -> List[TimelineEvent]:
        # Sort chronologically
        events = cls._timelines.get(claim_id, [])
        return sorted(events, key=lambda x: x.timestamp)
