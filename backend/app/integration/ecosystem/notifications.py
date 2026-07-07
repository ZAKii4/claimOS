import uuid
from typing import Dict, List, Any
from datetime import datetime
from app.integration.core.models import Notification, NotificationChannel


class NotificationManager:
    """Manages multi-channel notifications with templates."""

    _notifications: List[Notification] = []
    _templates: Dict[str, str] = {
        "claim_approved": "Bonjour {name}, votre dossier {claim_id} a été approuvé.",
        "fraud_alert": "ALERTE: Fraude détectée sur le dossier {claim_id}.",
    }

    @classmethod
    def send(
        cls, 
        tenant_id: str, 
        channel: NotificationChannel, 
        recipient: str, 
        template_id: str, 
        context: Dict[str, Any]
    ) -> Notification:
        notification = Notification(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            channel=channel,
            recipient=recipient,
            template_id=template_id,
            context=context,
        )

        template = cls._templates.get(template_id)
        if not template:
            notification.status = "FAILED"
        else:
            # Render template (stub)
            try:
                rendered = template.format(**context)
                notification.status = "SENT"
                notification.sent_at = datetime.utcnow()
            except KeyError:
                notification.status = "FAILED"

        cls._notifications.append(notification)
        return notification

    @classmethod
    def get_history(cls, tenant_id: str = None) -> List[Notification]:
        if tenant_id:
            return [n for n in cls._notifications if n.tenant_id == tenant_id]
        return list(cls._notifications)
