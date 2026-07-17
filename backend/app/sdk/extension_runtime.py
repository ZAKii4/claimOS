from typing import Dict, Any, List
import uuid

from app.sdk.plugin_sdk import PluginSDK

class ExtensionRuntime:
    """Manages dynamic loading, isolation, and lifecycle of plugins."""

    _active_plugins: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def install(cls, manifest: Dict[str, Any]) -> Dict[str, Any]:
        if not PluginSDK.validate_manifest(manifest):
            raise ValueError("Invalid plugin manifest.")
        
        p_id = str(uuid.uuid4())
        plugin = {
            "id": p_id,
            "manifest": manifest,
            "status": "INSTALLED"
        }
        cls._active_plugins[p_id] = plugin
        return plugin

    @classmethod
    def enable(cls, plugin_id: str) -> bool:
        if plugin_id in cls._active_plugins:
            cls._active_plugins[plugin_id]["status"] = "ENABLED"
            return True
        return False

    @classmethod
    def disable(cls, plugin_id: str) -> bool:
        if plugin_id in cls._active_plugins:
            cls._active_plugins[plugin_id]["status"] = "DISABLED"
            return True
        return False

    @classmethod
    def get_all(cls) -> List[Dict[str, Any]]:
        return list(cls._active_plugins.values())

    @classmethod
    def _reset(cls):
        cls._active_plugins.clear()
