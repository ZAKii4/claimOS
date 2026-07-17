from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any

from app.devops.environments import EnvironmentManager
from app.devops.releases import ReleaseManager
from app.devops.migrations import MigrationEngine
from app.devops.deployment import DeploymentManager
from app.devops.incidents import IncidentManager
from app.devops.runbooks import RunbookManager
from app.devops.changes import ChangeManager
from app.devops.security import SecurityScanner
from app.devops.dependencies import DependencyManager
from app.devops.production import ProductionManager
from app.devops.chaos import ChaosEngine
from app.devops.backup import BackupManager

router = APIRouter(prefix="/devops", tags=["Enterprise DevSecOps"])


class DeployRequest(BaseModel):
    version: str
    strategy: str = "ROLLING"
    environment: str = "production"

class RollbackRequest(BaseModel):
    deployment_id: str

class IncidentRequest(BaseModel):
    title: str
    severity: str
    impact: str

class ChaosRequest(BaseModel):
    failure_type: str
    resolve: bool = False

class BackupReq(BaseModel):
    type: str = "FULL"

class RestoreReq(BaseModel):
    backup_id: str


@router.get("/environments")
def get_environments():
    return EnvironmentManager.get_environments()

@router.get("/releases")
def get_releases():
    return ReleaseManager.get_releases()

@router.post("/deploy")
def post_deploy(req: DeployRequest):
    return DeploymentManager.deploy(req.version, req.strategy, req.environment)

@router.post("/rollback")
def post_rollback(req: RollbackRequest):
    return {"success": DeploymentManager.rollback(req.deployment_id)}

@router.get("/incidents")
def get_incidents():
    return IncidentManager.get_incidents()

@router.post("/incidents")
def post_incident(req: IncidentRequest):
    return IncidentManager.report_incident(req.title, req.severity, req.impact)

@router.get("/runbooks")
def get_runbooks():
    return RunbookManager.get_runbooks()

@router.get("/changes")
def get_changes():
    return ChangeManager.get_changes()

@router.get("/security")
def get_security():
    return SecurityScanner.scan()

@router.get("/dependencies")
def get_dependencies():
    return DependencyManager.get_report()

@router.get("/production")
def get_production():
    return ProductionManager.get_health()

@router.post("/chaos/run")
def run_chaos(req: ChaosRequest):
    if req.resolve:
        return {"success": ChaosEngine.resolve_failure(req.failure_type)}
    return {"success": ChaosEngine.inject_failure(req.failure_type)}

@router.post("/backup")
def run_backup(req: BackupReq):
    return BackupManager.create_backup(req.type)

@router.post("/restore")
def run_restore(req: RestoreReq):
    return {"success": BackupManager.restore(req.backup_id)}
