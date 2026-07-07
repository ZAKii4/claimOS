from typing import Dict, List, Optional, Callable
from app.platform.tenant.models import PluginInfo


class PluginManager:
    """Discovery, registration, and lifecycle management for plugins."""

    _plugins: Dict[str, PluginInfo] = {}
    _hooks: Dict[str, List[Callable]] = {}  # hook_name -> list of callables

    @classmethod
    def register(cls, plugin: PluginInfo):
        cls._plugins[plugin.name] = plugin

    @classmethod
    def unregister(cls, name: str):
        cls._plugins.pop(name, None)

    @classmethod
    def get_all(cls) -> List[PluginInfo]:
        return list(cls._plugins.values())

    @classmethod
    def get_active(cls) -> List[PluginInfo]:
        return [p for p in cls._plugins.values() if p.active]

    @classmethod
    def get_by_capability(cls, capability: str) -> List[PluginInfo]:
        return [p for p in cls._plugins.values() if capability in p.provides and p.active]

    @classmethod
    def register_hook(cls, hook_name: str, callback: Callable):
        cls._hooks.setdefault(hook_name, []).append(callback)

    @classmethod
    def execute_hook(cls, hook_name: str, *args, **kwargs) -> List:
        results = []
        for cb in cls._hooks.get(hook_name, []):
            results.append(cb(*args, **kwargs))
        return results

    @classmethod
    def reload(cls):
        """Re-discover and reload all plugins (placeholder for dynamic loading)."""
        for p in cls._plugins.values():
            p.active = True
