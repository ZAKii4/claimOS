from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any

from app.integration.core.bus import IntegrationEventBus
from app.integration.core.models import EventType
from app.integration.connectors.manager import ConnectorFramework
from app.integration.data.sync import SynchronizationEngine
from app.integration.ecosystem.notifications import NotificationManager, NotificationChannel
from app.integration.ecosystem.marketplace import MarketplaceManager, MarketplaceExtension
from app.integration.ecosystem.sdk_generator import SDKGenerator

router = APIRouter(prefix="/integrations", tags=["Enterprise Integration Hub"])


class SyncReq(BaseModel):
    tenant_id: str
    connector_id: str
    endpoint: str
    data: List[Dict[str, Any]]


class WebhookReq(BaseModel):
    url: str
    events: List[EventType]


class InstallExtensionReq(BaseModel):
    extension_id: str
    public_key: str = "secret"


@router.get("/connectors")
def list_connectors():
    return [{"id": c.id, "name": c.name} for c in ConnectorFramework.get_all()]


@router.post("/sync")
def trigger_sync(req: SyncReq):
    result = SynchronizationEngine.sync_to_external(
        req.tenant_id, req.connector_id, req.endpoint, req.data
    )
    return result.model_dump()


@router.get("/events")
def list_events(tenant_id: str = None):
    return [e.model_dump() for e in IntegrationEventBus.get_history(tenant_id)]


@router.post("/webhooks")
def register_webhook(req: WebhookReq):
    # Webhook registration stub
    return {"status": "registered", "url": req.url, "events": req.events}


@router.get("/notifications")
def list_notifications(tenant_id: str = None):
    return [n.model_dump() for n in NotificationManager.get_history(tenant_id)]


@router.get("/marketplace")
def list_catalog():
    return [e.model_dump() for e in MarketplaceManager.get_catalog()]


@router.post("/marketplace/install")
def install_extension(req: InstallExtensionReq):
    try:
        success = MarketplaceManager.install(req.extension_id, req.public_key)
        return {"installed": success}
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sdk")
def get_sdk():
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(SDKGenerator.generate_python_sdk())


@router.get("/openapi")
def get_openapi():
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(SDKGenerator.generate_openapi())
