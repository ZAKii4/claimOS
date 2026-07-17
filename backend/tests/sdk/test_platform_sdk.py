import pytest
from fastapi.testclient import TestClient
from app.main import app

from app.sdk.plugin_sdk import PluginSDK
from app.sdk.extension_runtime import ExtensionRuntime
from app.sdk.hook_manager import HookManager
from app.sdk.event_sdk import EventSDK
from app.sdk.cli import ClaimCTL
from app.sdk.generator import ProjectGenerator
from app.sdk.documentation import DocumentationManager
from app.sdk.marketplace import MarketplaceV2
from app.sdk.testing import SDKTestingFramework

client = TestClient(app)

# ────────────────────────────────────────────────────────
# Core SDK Tests
# ────────────────────────────────────────────────────────

def test_plugin_sdk():
    manifest = PluginSDK.create_manifest_template()
    assert PluginSDK.validate_manifest(manifest)
    
    invalid = {"name": "foo"}
    assert not PluginSDK.validate_manifest(invalid)

def test_extension_runtime():
    ExtensionRuntime._reset()
    manifest = PluginSDK.create_manifest_template()
    plugin = ExtensionRuntime.install(manifest)
    assert plugin["status"] == "INSTALLED"
    
    assert ExtensionRuntime.enable(plugin["id"])
    assert ExtensionRuntime.get_all()[0]["status"] == "ENABLED"
    
    assert ExtensionRuntime.disable(plugin["id"])
    assert ExtensionRuntime.get_all()[0]["status"] == "DISABLED"

def test_hook_manager():
    HookManager._reset()
    assert HookManager.register_hook("Before OCR", "plugin-123")
    assert "plugin-123" in HookManager.get_hooks()["Before OCR"]
    assert not HookManager.register_hook("Invalid Hook", "plugin")

def test_event_sdk():
    EventSDK._reset()
    evt = EventSDK.publish("ClaimCreated", {"id": "CLM-001"})
    assert evt["type"] == "ClaimCreated"
    assert len(EventSDK.get_events()) == 1

def test_cli():
    assert "1.0.0" in ClaimCTL.execute("claimctl version")
    assert "operational" in ClaimCTL.execute("claimctl health")
    assert "Error" in ClaimCTL.execute("invalid")

def test_project_generator():
    res = ProjectGenerator.generate_template("ocr")
    assert res["status"] == "SUCCESS"
    assert "main.py" in res["template"]["files"]
    
    assert ProjectGenerator.generate_template("invalid")["status"] == "ERROR"

def test_documentation_manager():
    docs = DocumentationManager.generate_docs()
    assert "api_docs" in docs

def test_marketplace():
    items = MarketplaceV2.get_marketplace_items()
    assert len(items) > 0

def test_testing_framework():
    res = SDKTestingFramework.run_suite("plug-1")
    assert res["status"] == "PASS"

# ────────────────────────────────────────────────────────
# API Endpoint Tests
# ────────────────────────────────────────────────────────

def test_api_endpoints():
    ExtensionRuntime._reset()
    EventSDK._reset()

    # Plugins
    manifest = PluginSDK.create_manifest_template()
    res = client.post("/api/v1/platform-sdk/plugins/install", json=manifest)
    assert res.status_code == 200
    p_id = res.json()["id"]

    assert client.get("/api/v1/platform-sdk/plugins").status_code == 200
    res = client.post(f"/api/v1/platform-sdk/plugins/uninstall?plugin_id={p_id}")
    assert res.status_code == 200

    # Hooks & Events
    assert client.get("/api/v1/platform-sdk/hooks").status_code == 200
    
    res = client.post("/api/v1/platform-sdk/events/publish", json={"type": "Test", "payload": {}})
    assert res.status_code == 200
    assert client.get("/api/v1/platform-sdk/events").status_code == 200

    # Generators & Utils
    assert client.get("/api/v1/platform-sdk/sdk").status_code == 200
    assert client.get("/api/v1/platform-sdk/templates?type=ocr").status_code == 200
    assert client.get("/api/v1/platform-sdk/documentation").status_code == 200
    assert client.get("/api/v1/platform-sdk/examples").status_code == 200
    assert client.get("/api/v1/platform-sdk/marketplace").status_code == 200

    res = client.post("/api/v1/platform-sdk/cli/run", json={"command": "claimctl version"})
    assert res.status_code == 200
    assert "1.0.0" in res.json()["output"]

    assert client.get("/api/v1/platform-sdk/testing/run?plugin_id=123").status_code == 200
