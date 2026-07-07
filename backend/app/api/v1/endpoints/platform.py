from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any

from app.platform.tenant.resolver import TenantResolver
from app.platform.tenant.models import Tenant
from app.platform.config.features import FeatureFlagEngine
from app.platform.plugins.manager import PluginManager
from app.platform.cluster.nodes import NodeManager
from app.platform.cluster.scaling import AutoScalingEngine
from app.platform.deployment.backup import BackupManager
from app.platform.deployment.deployer import DeploymentManager
from app.platform.deployment.billing import BillingEngine
from app.platform.tasks.engine import TaskQueue

router = APIRouter(prefix="/platform", tags=["Enterprise Cloud Platform"])


class CreateTenantReq(BaseModel):
    name: str
    slug: str


class BackupReq(BaseModel):
    data: Dict[str, Any]
    tenant_id: str = "global"


@router.get("/tenants")
def list_tenants():
    return [t.model_dump() for t in TenantResolver.get_all_tenants()]


@router.post("/tenants")
def create_tenant(req: CreateTenantReq):
    import uuid
    tenant = Tenant(id=str(uuid.uuid4()), name=req.name, slug=req.slug)
    TenantResolver.register_tenant(tenant)
    return tenant.model_dump()


@router.get("/features")
def list_features():
    return [f.model_dump() for f in FeatureFlagEngine.get_all()]


@router.post("/plugins/reload")
def reload_plugins():
    PluginManager.reload()
    return {"status": "reloaded", "count": len(PluginManager.get_active())}


@router.get("/workers")
def list_workers():
    return [n.model_dump() for n in NodeManager.get_all_nodes()]


@router.get("/deployment/status")
def deployment_status():
    return DeploymentManager.get_status().model_dump()


@router.post("/backup")
def create_backup(req: BackupReq):
    entry = BackupManager.create_backup(req.data, req.tenant_id)
    return {"backup_id": entry.id, "checksum": entry.checksum}


@router.post("/restore/{backup_id}")
def restore_backup(backup_id: str):
    data = BackupManager.restore(backup_id)
    if not data:
        from fastapi import HTTPException
        raise HTTPException(404, "Backup not found")
    return {"restored": True, "data": data}


@router.get("/billing")
def get_billing():
    return [u.model_dump() for u in BillingEngine.get_all_usage()]


@router.get("/scaling")
def get_scaling():
    rec = AutoScalingEngine.evaluate(queue_length=TaskQueue.get_queue_size())
    return rec.model_dump()
