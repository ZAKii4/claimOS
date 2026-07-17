import pytest
from fastapi.testclient import TestClient
from app.main import app

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

client = TestClient(app)

# ────────────────────────────────────────────────────────
# 1. EnvironmentManager Tests
# ────────────────────────────────────────────────────────

def test_environments_get():
    EnvironmentManager._reset()
    envs = EnvironmentManager.get_environments()
    assert len(envs) == 4
    assert any(e["name"] == "production" for e in envs)

def test_environment_update():
    EnvironmentManager._reset()
    EnvironmentManager.update_environment("local", {"url": "http://127.0.0.1"})
    env = EnvironmentManager.get_environment("local")
    assert env["url"] == "http://127.0.0.1"

def test_environment_update_fail():
    assert not EnvironmentManager.update_environment("unknown", {"url": ""})

# ────────────────────────────────────────────────────────
# 2. ReleaseManager Tests
# ────────────────────────────────────────────────────────

def test_releases():
    ReleaseManager._reset()
    r = ReleaseManager.create_release("v2.0", "admin", "abc123chk")
    assert r["version"] == "v2.0"
    rels = ReleaseManager.get_releases()
    assert len(rels) == 1

# ────────────────────────────────────────────────────────
# 3. MigrationEngine Tests
# ────────────────────────────────────────────────────────

def test_migrations():
    MigrationEngine._reset()
    assert MigrationEngine.upgrade("v1.1")
    assert MigrationEngine._current_version == "v1.1"
    assert MigrationEngine.downgrade("v1.0")
    status = MigrationEngine.get_status()
    assert status["current_version"] == "v1.0"
    assert len(status["history"]) == 2

# ────────────────────────────────────────────────────────
# 4. DeploymentManager Tests
# ────────────────────────────────────────────────────────

def test_deployments():
    DeploymentManager._reset()
    d = DeploymentManager.deploy("v2.0", "CANARY")
    assert d["status"] == "DEPLOYED"
    assert d["strategy"] == "CANARY"
    
    assert DeploymentManager.rollback(d["id"])
    assert not DeploymentManager.rollback("invalid")
    
    deps = DeploymentManager.get_deployments()
    assert deps[0]["status"] == "ROLLED_BACK"

# ────────────────────────────────────────────────────────
# 5. IncidentManager Tests
# ────────────────────────────────────────────────────────

def test_incidents():
    IncidentManager._reset()
    inc = IncidentManager.report_incident("DB Slow", "High", "Critical")
    assert inc["status"] == "OPEN"
    
    assert IncidentManager.resolve_incident(inc["id"], "Fixed index")
    assert not IncidentManager.resolve_incident("invalid", "...")
    
    incs = IncidentManager.get_incidents()
    assert incs[0]["status"] == "RESOLVED"

# ────────────────────────────────────────────────────────
# 6. RunbookManager Tests
# ────────────────────────────────────────────────────────

def test_runbooks():
    RunbookManager._reset()
    rb = RunbookManager.create_runbook("Restart Worker", ["Step 1", "Step 2"])
    assert rb["title"] == "Restart Worker"
    assert len(RunbookManager.get_runbooks()) == 1

# ────────────────────────────────────────────────────────
# 7. ChangeManager Tests
# ────────────────────────────────────────────────────────

def test_changes():
    ChangeManager._reset()
    ch = ChangeManager.propose_change("Add feature", "Low")
    assert ch["status"] == "PENDING_APPROVAL"
    
    assert ChangeManager.approve_change(ch["id"])
    assert not ChangeManager.approve_change("invalid")
    
    changes = ChangeManager.get_changes()
    assert changes[0]["status"] == "APPROVED"

# ────────────────────────────────────────────────────────
# 8. SecurityScanner & DependencyManager Tests
# ────────────────────────────────────────────────────────

def test_security_scanner():
    report = SecurityScanner.scan()
    assert report["status"] == "PASS"

def test_dependency_manager():
    report = DependencyManager.get_report()
    assert report["status"] == "HEALTHY"

# ────────────────────────────────────────────────────────
# 9. ProductionManager Tests
# ────────────────────────────────────────────────────────

def test_production_manager():
    health = ProductionManager.get_health()
    assert health["status"] == "HEALTHY"
    assert health["nodes"] == 5

# ────────────────────────────────────────────────────────
# 10. ChaosEngine Tests
# ────────────────────────────────────────────────────────

def test_chaos_engine():
    ChaosEngine._reset()
    assert ChaosEngine.inject_failure("LLM_FAILURE")
    assert ChaosEngine.get_status()["LLM_FAILURE"] is True
    assert not ChaosEngine.inject_failure("INVALID")
    
    assert ChaosEngine.resolve_failure("LLM_FAILURE")
    assert ChaosEngine.get_status()["LLM_FAILURE"] is False

# ────────────────────────────────────────────────────────
# 11. BackupManager Tests
# ────────────────────────────────────────────────────────

def test_backup_manager():
    BackupManager._reset()
    b = BackupManager.create_backup("INCREMENTAL")
    assert b["type"] == "INCREMENTAL"
    
    assert BackupManager.restore(b["id"])
    assert not BackupManager.restore("invalid")
    
    assert len(BackupManager.get_backups()) == 1

# ────────────────────────────────────────────────────────
# 12. API Endpoint Tests
# ────────────────────────────────────────────────────────

def test_api_endpoints():
    assert client.get("/api/v1/devops/environments").status_code == 200
    assert client.get("/api/v1/devops/releases").status_code == 200
    
    res = client.post("/api/v1/devops/deploy", json={"version": "v1.0"})
    assert res.status_code == 200
    dep_id = res.json()["id"]
    
    res = client.post("/api/v1/devops/rollback", json={"deployment_id": dep_id})
    assert res.json()["success"] is True

    assert client.get("/api/v1/devops/incidents").status_code == 200
    res = client.post("/api/v1/devops/incidents", json={"title": "T", "severity": "S", "impact": "I"})
    assert res.status_code == 200

    assert client.get("/api/v1/devops/runbooks").status_code == 200
    assert client.get("/api/v1/devops/changes").status_code == 200
    assert client.get("/api/v1/devops/security").status_code == 200
    assert client.get("/api/v1/devops/dependencies").status_code == 200
    assert client.get("/api/v1/devops/production").status_code == 200

    res = client.post("/api/v1/devops/chaos/run", json={"failure_type": "DB_TIMEOUT", "resolve": False})
    assert res.json()["success"] is True

    res = client.post("/api/v1/devops/backup", json={"type": "FULL"})
    assert res.status_code == 200
    b_id = res.json()["id"]

    res = client.post("/api/v1/devops/restore", json={"backup_id": b_id})
    assert res.json()["success"] is True
