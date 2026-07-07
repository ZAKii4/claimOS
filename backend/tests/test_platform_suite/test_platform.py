import pytest
import time
from app.platform.tenant.models import Tenant, TenantContext, FeatureFlag, PluginInfo, DeploymentMode
from app.platform.tenant.resolver import TenantResolver
from app.platform.tenant.isolation import TenantResourceStore
from app.platform.config.hierarchy import ConfigHierarchy
from app.platform.config.features import FeatureFlagEngine
from app.platform.plugins.manager import PluginManager
from app.platform.tasks.engine import TaskQueue, TaskState
from app.platform.cluster.nodes import NodeManager, NodeStatus
from app.platform.cluster.scaling import AutoScalingEngine
from app.platform.gateway.gateway import APIGateway
from app.platform.deployment.backup import BackupManager
from app.platform.deployment.deployer import DeploymentManager
from app.platform.deployment.billing import BillingEngine


# ─────────────────────────────────────────────────────
# 1. Multi-Tenant Core & Isolation
# ─────────────────────────────────────────────────────

def test_tenant_registration():
    tenant = Tenant(id="t1", name="Alpha Insure", slug="alpha")
    TenantResolver.register_tenant(tenant)
    assert TenantResolver.get_tenant("t1") is not None
    assert len(TenantResolver.get_all_tenants()) > 0


def test_tenant_resolver_subdomain():
    tenant = Tenant(id="t2", name="Beta Insure", slug="beta")
    TenantResolver.register_tenant(tenant)
    ctx = TenantResolver.resolve_from_subdomain("beta")
    assert ctx is not None
    assert ctx.tenant_id == "t2"


def test_tenant_resolver_api_key():
    TenantResolver.register_api_key("sk_beta123", "t2")
    ctx = TenantResolver.resolve_from_api_key("sk_beta123")
    assert ctx is not None
    assert ctx.tenant_id == "t2"


def test_tenant_resource_isolation():
    # Tenant A
    TenantResourceStore.store("t_A", "claims", {"id": "C1"})
    TenantResourceStore.store("t_A", "claims", {"id": "C2"})

    # Tenant B
    TenantResourceStore.store("t_B", "claims", {"id": "C3"})

    assert len(TenantResourceStore.get("t_A", "claims")) == 2
    assert len(TenantResourceStore.get("t_B", "claims")) == 1

    # Cross-tenant is structurally impossible via the API
    assert TenantResourceStore.get("t_A", "claims")[0]["id"] == "C1"


def test_tenant_clear_data():
    TenantResourceStore.store("t_C", "docs", {"id": "D1"})
    TenantResourceStore.clear_tenant("t_C")
    assert len(TenantResourceStore.get("t_C", "docs")) == 0


# ─────────────────────────────────────────────────────
# 2. Config Hierarchy
# ─────────────────────────────────────────────────────

def test_config_hierarchy_global():
    ConfigHierarchy.set_global("llm_model", "gpt-3.5")
    assert ConfigHierarchy.get("llm_model") == "gpt-3.5"


def test_config_hierarchy_tenant_override():
    ConfigHierarchy.set_global("llm_model", "gpt-3.5")
    ConfigHierarchy.set_tenant("t_premium", "llm_model", "gpt-4")

    assert ConfigHierarchy.get("llm_model", tenant_id="t_standard") == "gpt-3.5"
    assert ConfigHierarchy.get("llm_model", tenant_id="t_premium") == "gpt-4"


def test_config_hierarchy_env_override():
    ConfigHierarchy.set_environment("staging", "llm_model", "mock-llm")
    assert ConfigHierarchy.get("llm_model", env="staging") == "mock-llm"


def test_config_hierarchy_runtime_override():
    ConfigHierarchy.set_override("llm_model", "claude-3")
    assert ConfigHierarchy.get("llm_model") == "claude-3"
    # Cleanup for other tests
    ConfigHierarchy._overrides.clear()


# ─────────────────────────────────────────────────────
# 3. Feature Flags
# ─────────────────────────────────────────────────────

def test_feature_flag_global():
    flag = FeatureFlag(name="new_ui", enabled=True)
    FeatureFlagEngine.register(flag)
    assert FeatureFlagEngine.is_enabled("new_ui") is True


def test_feature_flag_tenant_override():
    flag = FeatureFlag(name="multi_agent", enabled=False, tenant_overrides={"t_premium": True})
    FeatureFlagEngine.register(flag)
    assert FeatureFlagEngine.is_enabled("multi_agent", tenant_id="t_standard") is False
    assert FeatureFlagEngine.is_enabled("multi_agent", tenant_id="t_premium") is True


def test_feature_flag_user_override():
    flag = FeatureFlag(name="debug_mode", enabled=False, user_overrides={"admin1": True})
    FeatureFlagEngine.register(flag)
    assert FeatureFlagEngine.is_enabled("debug_mode", user_id="user1") is False
    assert FeatureFlagEngine.is_enabled("debug_mode", user_id="admin1") is True


def test_feature_flag_rollout():
    # 0% rollout -> disabled
    f0 = FeatureFlag(name="roll0", enabled=True, rollout_percentage=0.0)
    FeatureFlagEngine.register(f0)
    assert FeatureFlagEngine.is_enabled("roll0", user_id="u1") is False

    # 100% rollout -> enabled
    f100 = FeatureFlag(name="roll100", enabled=True, rollout_percentage=100.0)
    FeatureFlagEngine.register(f100)
    assert FeatureFlagEngine.is_enabled("roll100", user_id="u1") is True


# ─────────────────────────────────────────────────────
# 4. Plugin Architecture
# ─────────────────────────────────────────────────────

def test_plugin_registration():
    p = PluginInfo(name="google_vision", provides=["ocr_provider"])
    PluginManager.register(p)
    assert len(PluginManager.get_by_capability("ocr_provider")) > 0


def test_plugin_hook_execution():
    def hook_a(data):
        return data + 1

    def hook_b(data):
        return data * 2

    PluginManager.register_hook("process_data", hook_a)
    PluginManager.register_hook("process_data", hook_b)

    results = PluginManager.execute_hook("process_data", 5)
    assert results == [6, 10]


def test_plugin_reload():
    p = PluginInfo(name="test_plugin", active=False)
    PluginManager.register(p)
    PluginManager.reload()
    assert PluginManager.get_active()[-1].name == "test_plugin"


# ─────────────────────────────────────────────────────
# 5. Distributed Task Engine
# ─────────────────────────────────────────────────────

def dummy_task_handler(payload):
    if payload.get("fail"):
        raise ValueError("Simulated failure")
    return payload.get("val", 0) * 2


def test_task_queue_success():
    TaskQueue.register_handler("math", dummy_task_handler)
    TaskQueue.enqueue("math", {"val": 5})

    task = TaskQueue.process_next()
    assert task.state == TaskState.COMPLETED
    assert task.result == 10


def test_task_queue_retry_and_dlq():
    TaskQueue.register_handler("math_fail", dummy_task_handler)
    TaskQueue.enqueue("math_fail", {"fail": True})

    # Try 1
    t1 = TaskQueue.process_next()
    assert t1.state == TaskState.RETRYING
    assert t1.retries == 1

    # Try 2
    t2 = TaskQueue.process_next()
    assert t2.retries == 2

    # Try 3 (max) -> goes to DLQ
    t3 = TaskQueue.process_next()
    assert t3.state == TaskState.DEAD

    assert len(TaskQueue.get_dlq()) > 0


def test_task_queue_priority():
    TaskQueue.enqueue("math", {"val": 1}, priority=10)
    TaskQueue.enqueue("math", {"val": 2}, priority=50) # Should be processed first

    t = TaskQueue.process_next()
    assert t.payload["val"] == 2


# ─────────────────────────────────────────────────────
# 6. Cluster & Node Manager
# ─────────────────────────────────────────────────────

def test_node_registration_leader_election():
    # Reset
    NodeManager._nodes.clear()
    NodeManager._leader_id = None

    n1 = NodeManager.register("10.0.0.1")
    assert n1.is_leader is True
    assert NodeManager.get_leader().id == n1.id

    n2 = NodeManager.register("10.0.0.2")
    assert n2.is_leader is False


def test_node_failover():
    n1 = NodeManager.get_leader()
    NodeManager.mark_down(n1.id)

    new_leader = NodeManager.get_leader()
    assert new_leader is not None
    assert new_leader.id != n1.id
    assert new_leader.is_leader is True


def test_node_load_balancing():
    NodeManager._nodes.clear()
    NodeManager._leader_id = None
    n1 = NodeManager.register("10.0.0.1")
    n2 = NodeManager.register("10.0.0.2")
    
    # Mock load
    NodeManager.heartbeat(n1.id, tasks=10)
    NodeManager.heartbeat(n2.id, tasks=0)
    # The other node has 0 tasks, should be selected
    least_loaded = NodeManager.get_least_loaded()
    assert least_loaded.id == n2.id
    assert least_loaded.task_count == 0


# ─────────────────────────────────────────────────────
# 7. API Gateway
# ─────────────────────────────────────────────────────

def test_api_gateway_rate_limiting():
    APIGateway._rate_limits.clear()
    tenant = "t_rate"

    # Allow 2 requests
    assert APIGateway.check_rate_limit(tenant, limit=2) is True
    assert APIGateway.check_rate_limit(tenant, limit=2) is True

    # Block 3rd
    assert APIGateway.check_rate_limit(tenant, limit=2) is False

    usage = APIGateway.get_usage(tenant)
    assert usage["used"] == 2
    assert usage["remaining"] == 0


# ─────────────────────────────────────────────────────
# 8. Backup & Restore
# ─────────────────────────────────────────────────────

def test_backup_create_restore():
    data = {"claims": [{"id": "C1"}], "users": ["alice"]}
    backup = BackupManager.create_backup(data, tenant_id="t_backup")

    assert backup.id is not None
    assert backup.checksum != ""

    restored = BackupManager.restore(backup.id)
    assert restored["claims"][0]["id"] == "C1"


def test_backup_integrity():
    data = {"test": 123}
    backup = BackupManager.create_backup(data)

    assert BackupManager.verify_integrity(backup.id) is True

    # Simulate tampering
    backup.data["test"] = 999
    assert BackupManager.verify_integrity(backup.id) is False


# ─────────────────────────────────────────────────────
# 9. Billing Engine
# ─────────────────────────────────────────────────────

def test_billing_engine():
    BillingEngine._usage.clear()
    tenant = "t_bill"

    BillingEngine.record_ocr(tenant, 100) # 100 * 0.02 = 2.0
    BillingEngine.record_llm(tenant, 50)  # 50 * 0.05 = 2.5
    BillingEngine.record_storage(tenant, 1000) # 1000 * 0.001 = 1.0
    BillingEngine.record_claim(tenant, 10) # 10 * 0.10 = 1.0

    usage = BillingEngine.get_usage(tenant)
    assert usage.ocr_calls == 100
    assert usage.llm_calls == 50
    assert usage.total_cost == 6.5


# ─────────────────────────────────────────────────────
# 10. Auto Scaling
# ─────────────────────────────────────────────────────

def test_auto_scaling_scale_out_cpu():
    NodeManager._nodes.clear()
    NodeManager._leader_id = None
    n = NodeManager.register("10.0.0.1")
    NodeManager.heartbeat(n.id, cpu=90.0) # High CPU

    rec = AutoScalingEngine.evaluate()
    assert rec.action == "scale_out"


def test_auto_scaling_scale_out_queue():
    NodeManager.heartbeat(NodeManager.get_leader().id, cpu=50.0) # Normal CPU
    rec = AutoScalingEngine.evaluate(queue_length=100) # High Queue
    assert rec.action == "scale_out"


def test_auto_scaling_scale_in():
    n2 = NodeManager.register("10.0.0.2")
    NodeManager.heartbeat(NodeManager.get_leader().id, cpu=10.0)
    NodeManager.heartbeat(n2.id, cpu=10.0)

    rec = AutoScalingEngine.evaluate(queue_length=0)
    assert rec.action == "scale_in"


# ─────────────────────────────────────────────────────
# 11. Deployment Manager
# ─────────────────────────────────────────────────────

def test_deployment_manager():
    DeploymentManager.set_mode(DeploymentMode.KUBERNETES)
    assert DeploymentManager.get_status().mode == DeploymentMode.KUBERNETES

    assert "FROM python" in DeploymentManager.generate_dockerfile()
    assert "version:" in DeploymentManager.generate_docker_compose()
    assert "kind: Deployment" in DeploymentManager.generate_k8s_deployment()
    assert "replicaCount:" in DeploymentManager.generate_helm_values()
