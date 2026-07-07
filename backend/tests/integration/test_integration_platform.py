import pytest
from app.integration.core.bus import IntegrationEventBus
from app.integration.core.models import EventType, MarketplaceExtension, MarketplaceExtensionType
from app.integration.connectors.manager import ConnectorFramework
from app.integration.connectors.implementations import CRMConnector, ERPConnector, RESTConnector
from app.integration.data.transformer import TransformationEngine
from app.integration.data.sync import SynchronizationEngine
from app.integration.api_manager.client import APIIntegrationManager, CircuitBreakerError
from app.integration.api_manager.workflow import ExternalWorkflowStep
from app.integration.ecosystem.notifications import NotificationManager, NotificationChannel
from app.integration.ecosystem.marketplace import MarketplaceManager
from app.integration.ecosystem.sdk_generator import SDKGenerator


# ─────────────────────────────────────────────────────
# 1. Connectors & Framework
# ─────────────────────────────────────────────────────

def test_connector_registration():
    ConnectorFramework._connectors.clear()
    crm = CRMConnector()
    ConnectorFramework.register(crm)
    
    assert len(ConnectorFramework.get_all()) == 1
    assert ConnectorFramework.get("crm_01") is not None


def test_connector_activation():
    ConnectorFramework._tenant_activations.clear()
    ConnectorFramework.register(ERPConnector())
    
    ConnectorFramework.activate_for_tenant("t1", "erp_01")
    assert ConnectorFramework.is_active_for_tenant("t1", "erp_01") is True
    assert ConnectorFramework.is_active_for_tenant("t2", "erp_01") is False


def test_connector_connect_and_auth():
    rest = RESTConnector()
    assert rest.connect() is True
    assert rest.authenticate({"api_key": "123"}) is True
    assert rest.health_check() is True


def test_connector_send_receive():
    rest = RESTConnector()
    resp = rest.send("/api/test", {"data": 1})
    assert resp["data"] == {"data": 1}
    assert rest.receive("/api/test")["status"] == "received"


# ─────────────────────────────────────────────────────
# 2. Integration Event Bus
# ─────────────────────────────────────────────────────

def test_event_bus_publish():
    IntegrationEventBus._event_history.clear()
    event = IntegrationEventBus.publish("t1", EventType.CLAIM_CREATED, {"claim_id": "C01"})
    
    assert event.tenant_id == "t1"
    assert event.event_type == EventType.CLAIM_CREATED
    assert event.payload["claim_id"] == "C01"


def test_event_bus_subscribe():
    IntegrationEventBus._subscribers.clear()
    IntegrationEventBus._event_history.clear()
    
    calls = []
    def callback(evt):
        calls.append(evt)
        
    IntegrationEventBus.subscribe(EventType.FRAUD_DETECTED, callback)
    IntegrationEventBus.publish("t2", EventType.FRAUD_DETECTED, {})
    
    assert len(calls) == 1
    assert calls[0].event_type == EventType.FRAUD_DETECTED


def test_event_bus_history_isolation():
    IntegrationEventBus._event_history.clear()
    IntegrationEventBus.publish("t1", EventType.CLAIM_APPROVED, {})
    IntegrationEventBus.publish("t2", EventType.CLAIM_APPROVED, {})
    
    history_t1 = IntegrationEventBus.get_history("t1")
    assert len(history_t1) == 1
    assert history_t1[0].tenant_id == "t1"


# ─────────────────────────────────────────────────────
# 3. Data Transformation Engine
# ─────────────────────────────────────────────────────

def test_transformation_mapping():
    data = {"claim_id": "C123", "amount": 1500}
    mapping = {"claim_id": "externalReference", "amount": "totalAmount"}
    res = TransformationEngine.apply_mapping(data, mapping)
    
    assert "externalReference" in res
    assert "totalAmount" in res
    assert res["externalReference"] == "C123"


def test_transformation_type_conversion():
    data = {"amount": "1500.50"}
    res = TransformationEngine.transform_type(data, "amount", float)
    assert isinstance(res["amount"], float)
    assert res["amount"] == 1500.50


def test_transformation_to_json():
    res = TransformationEngine.to_json({"a": 1})
    assert res == '{"a": 1}'


def test_transformation_to_xml_stub():
    res = TransformationEngine.to_xml_stub({"a": 1})
    assert "<a>1</a>" in res


def test_transformation_to_csv_stub():
    res = TransformationEngine.to_csv_stub({"a": 1, "b": 2})
    lines = res.split("\n")
    assert lines[0] == "a,b"
    assert lines[1] == "1,2"


# ─────────────────────────────────────────────────────
# 4. Synchronization Engine
# ─────────────────────────────────────────────────────

def test_sync_engine_success():
    ConnectorFramework.register(RESTConnector())
    ConnectorFramework.activate_for_tenant("t1", "rest_01")
    
    data = [{"id": 1}, {"id": 2}]
    res = SynchronizationEngine.sync_to_external("t1", "rest_01", "/endpoint", data)
    
    assert res.status == "SUCCESS"
    assert res.records_synced == 2
    assert res.conflicts == 0


def test_sync_engine_unauthorized_connector():
    # Not activated for t3
    res = SynchronizationEngine.sync_to_external("t3", "rest_01", "/endpoint", [{"id": 1}])
    assert res.status == "FAILED"


def test_sync_engine_history():
    SynchronizationEngine._sync_history.clear()
    ConnectorFramework.activate_for_tenant("t2", "rest_01")
    SynchronizationEngine.sync_to_external("t2", "rest_01", "/endpoint", [{"id": 1}])
    
    hist = SynchronizationEngine.get_history("t2")
    assert len(hist) == 1


# ─────────────────────────────────────────────────────
# 5. API Integration Manager (Circuit Breaker)
# ─────────────────────────────────────────────────────

def test_api_manager_success():
    APIIntegrationManager.reset_circuit("endpoint_A")
    res = APIIntegrationManager.execute("endpoint_A", lambda: 42)
    assert res == 42


def test_api_manager_retry_and_circuit_open():
    APIIntegrationManager.reset_circuit("endpoint_B")
    APIIntegrationManager.RETRY_DELAY = 0.01  # speed up tests
    
    fail_count = [0]
    def failing_method():
        fail_count[0] += 1
        raise ValueError("Network Error")
        
    with pytest.raises(CircuitBreakerError):
        APIIntegrationManager.execute("endpoint_B", failing_method, retries=3)
        
    assert fail_count[0] == 3  # MAX_FAILURES
    assert APIIntegrationManager._circuit_state["endpoint_B"] == "OPEN"
    
    # Next call should fail immediately with OPEN
    with pytest.raises(CircuitBreakerError, match="Circuit OPEN"):
        APIIntegrationManager.execute("endpoint_B", failing_method)


# ─────────────────────────────────────────────────────
# 6. External Workflow Integration
# ─────────────────────────────────────────────────────

def test_external_workflow_step():
    ConnectorFramework.register(RESTConnector())
    ConnectorFramework.activate_for_tenant("t1", "rest_01")
    APIIntegrationManager.reset_circuit("/workflow/api")
    
    res = ExternalWorkflowStep.execute("t1", "rest_01", "/workflow/api", {"val": 99})
    assert res["data"] == {"val": 99}


# ─────────────────────────────────────────────────────
# 7. Notification Manager
# ─────────────────────────────────────────────────────

def test_notification_send_success():
    NotificationManager._notifications.clear()
    n = NotificationManager.send(
        "t1", NotificationChannel.EMAIL, "user@test.com", "claim_approved",
        {"name": "Alice", "claim_id": "C-100"}
    )
    
    assert n.status == "SENT"
    assert n.sent_at is not None
    assert n.recipient == "user@test.com"


def test_notification_send_missing_template():
    n = NotificationManager.send("t1", NotificationChannel.SMS, "123", "unknown", {})
    assert n.status == "FAILED"


def test_notification_history():
    NotificationManager._notifications.clear()
    NotificationManager.send("t2", NotificationChannel.SMS, "123", "claim_approved", {"name": "B", "claim_id": "1"})
    hist = NotificationManager.get_history("t2")
    assert len(hist) == 1


# ─────────────────────────────────────────────────────
# 8. Marketplace Manager
# ─────────────────────────────────────────────────────

def test_marketplace_publish_and_install():
    MarketplaceManager._catalog.clear()
    MarketplaceManager._installed.clear()
    
    ext = MarketplaceExtension(
        id="ext_1", name="Smart OCR", version="1.0", 
        vendor="Acme", type=MarketplaceExtensionType.OCR_ENGINE
    )
    
    MarketplaceManager.publish_to_catalog(ext, private_key_stub="my_secret")
    assert len(MarketplaceManager.get_catalog()) == 1
    
    success = MarketplaceManager.install("ext_1", public_key_stub="my_secret")
    assert success is True
    assert MarketplaceManager.get_installed()[0].installed is True


def test_marketplace_tamper_detection():
    ext = MarketplaceExtension(
        id="ext_2", name="Bad Extension", version="1.0", 
        vendor="Evil", type=MarketplaceExtensionType.VALIDATOR
    )
    MarketplaceManager.publish_to_catalog(ext, private_key_stub="wrong_secret")
    
    with pytest.raises(ValueError, match="Invalid signature"):
        MarketplaceManager.install("ext_2", public_key_stub="correct_secret")


# ─────────────────────────────────────────────────────
# 9. SDK Generator
# ─────────────────────────────────────────────────────

def test_sdk_generator_openapi():
    openapi = SDKGenerator.generate_openapi()
    assert "openapi: 3.1.0" in openapi
    assert "claimOS Enterprise" in openapi


def test_sdk_generator_python():
    sdk = SDKGenerator.generate_python_sdk()
    assert "class ClaimOSClient:" in sdk
    assert "def create_claim" in sdk


# Total tests = 4 (connector) + 3 (event bus) + 5 (transformer) + 3 (sync) + 2 (api manager) + 1 (workflow) + 3 (notifications) + 2 (marketplace) + 2 (sdk) = 25 tests.
# Wait, I wrote 25 tests. I will add more to reach ~34, or just update the tracker to 25.
# Let's add more to cover edge cases.

def test_connector_framework_missing():
    assert ConnectorFramework.get("missing_01") is None
    assert ConnectorFramework.is_active_for_tenant("t1", "missing_01") is False


def test_connector_get_active_for_tenant():
    ConnectorFramework._tenant_activations.clear()
    ConnectorFramework.activate_for_tenant("t1", "rest_01")
    active = ConnectorFramework.get_active_for_tenant("t1")
    assert len(active) == 1
    assert active[0].id == "rest_01"


def test_event_bus_no_subscribers_does_not_fail():
    IntegrationEventBus._subscribers.clear()
    evt = IntegrationEventBus.publish("t1", EventType.PAYMENT_COMPLETED, {})
    assert evt is not None


def test_transformation_type_conversion_missing_field():
    data = {"other": 1}
    res = TransformationEngine.transform_type(data, "amount", float)
    assert res == {"other": 1}


def test_sync_engine_connection_failed():
    class BadConnector(RESTConnector):
        def connect(self): return False
    
    bc = BadConnector()
    ConnectorFramework.register(bc)
    ConnectorFramework.activate_for_tenant("t1", bc.id)
    
    res = SynchronizationEngine.sync_to_external("t1", bc.id, "/ep", [{"id": 1}])
    assert res.status == "FAILED"
    assert res.details == "Connection failed."


def test_sync_engine_conflict_handling():
    class ConflictConnector(RESTConnector):
        def send(self, endpoint, payload): return {"status": "conflict"}
        
    cc = ConflictConnector()
    ConnectorFramework.register(cc)
    ConnectorFramework.activate_for_tenant("t1", cc.id)
    
    res = SynchronizationEngine.sync_to_external("t1", cc.id, "/ep", [{"id": 1}, {"id": 2}])
    assert res.status == "PARTIAL"
    assert res.conflicts == 2
    assert res.records_synced == 0


def test_api_manager_reset_works():
    APIIntegrationManager._circuit_state["ep_C"] = "OPEN"
    APIIntegrationManager.reset_circuit("ep_C")
    assert APIIntegrationManager._circuit_state["ep_C"] == "CLOSED"


def test_external_workflow_step_inactive_connector():
    ConnectorFramework._tenant_activations.clear()
    with pytest.raises(ValueError, match="not available"):
        ExternalWorkflowStep.execute("t1", "rest_01", "/api", {})


def test_notification_send_missing_context_var():
    n = NotificationManager.send("t1", NotificationChannel.EMAIL, "u@test.com", "claim_approved", {"wrong": 1})
    assert n.status == "FAILED"

# Now total is 25 + 9 = 34 tests. Perfect.
