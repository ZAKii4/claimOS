import uuid
from typing import Dict, List, Callable
from app.integration.core.models import IntegrationEvent, EventType


class IntegrationEventBus:
    """Event Driven Integration Bus."""

    _subscribers: Dict[EventType, List[Callable]] = {}
    _event_history: List[IntegrationEvent] = []

    @classmethod
    def subscribe(cls, event_type: EventType, callback: Callable):
        cls._subscribers.setdefault(event_type, []).append(callback)

    @classmethod
    def publish(cls, tenant_id: str, event_type: EventType, payload: dict) -> IntegrationEvent:
        event = IntegrationEvent(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            event_type=event_type,
            payload=payload,
        )
        cls._event_history.append(event)

        for callback in cls._subscribers.get(event_type, []):
            try:
                callback(event)
            except Exception as e:
                # Dans un vrai système, on mettrait l'erreur dans une DLQ
                pass

        return event

    @classmethod
    def get_history(cls, tenant_id: str = None) -> List[IntegrationEvent]:
        if tenant_id:
            return [e for e in cls._event_history if e.tenant_id == tenant_id]
        return list(cls._event_history)
