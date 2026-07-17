from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any

from app.sdk.plugin_sdk import PluginSDK
from app.sdk.extension_runtime import ExtensionRuntime
from app.sdk.hook_manager import HookManager
from app.sdk.event_sdk import EventSDK
from app.sdk.cli import ClaimCTL
from app.sdk.generator import ProjectGenerator
from app.sdk.documentation import DocumentationManager
from app.sdk.marketplace import MarketplaceV2
from app.sdk.testing import SDKTestingFramework

router = APIRouter(prefix="/platform-sdk", tags=["Platform SDK & Extensions"])

class PluginManifestReq(BaseModel):
    name: str
    version: str
    author: str
    permissions: List[str]

class EventReq(BaseModel):
    type: str
    payload: Dict[str, Any]

class CLIReq(BaseModel):
    command: str

@router.get("/plugins")
def get_plugins():
    return ExtensionRuntime.get_all()

@router.post("/plugins/install")
def install_plugin(req: PluginManifestReq):
    manifest = req.model_dump()
    return ExtensionRuntime.install(manifest)

@router.post("/plugins/uninstall")
def uninstall_plugin(plugin_id: str):
    # For now simply map uninstall to disable conceptually
    return {"success": ExtensionRuntime.disable(plugin_id)}

@router.get("/hooks")
def get_hooks():
    return HookManager.get_hooks()

@router.get("/events")
def get_events():
    return EventSDK.get_events()

@router.post("/events/publish")
def publish_event(req: EventReq):
    return EventSDK.publish(req.type, req.payload)

@router.get("/sdk")
def get_sdk_template():
    return PluginSDK.create_manifest_template()

@router.get("/templates")
def get_templates(type: str = "ocr"):
    return ProjectGenerator.generate_template(type)

@router.get("/documentation")
def get_documentation():
    return DocumentationManager.generate_docs()

@router.get("/examples")
def get_examples():
    return ProjectGenerator.generate_template("fraud")

@router.get("/marketplace")
def get_marketplace():
    return MarketplaceV2.get_marketplace_items()

@router.post("/cli/run")
def run_cli(req: CLIReq):
    return {"output": ClaimCTL.execute(req.command)}

@router.get("/testing/run")
def run_tests(plugin_id: str):
    return SDKTestingFramework.run_suite(plugin_id)
