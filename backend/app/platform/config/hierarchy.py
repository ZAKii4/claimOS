from typing import Dict, Any, Optional


class ConfigHierarchy:
    """
    Hierarchical configuration with override chain:
    Global → Tenant → Environment → Feature Flag → Runtime Override
    """

    _global: Dict[str, Any] = {}
    _tenant: Dict[str, Dict[str, Any]] = {}  # tenant_id -> settings
    _env: Dict[str, Dict[str, Any]] = {}     # env_name -> settings
    _overrides: Dict[str, Any] = {}

    @classmethod
    def set_global(cls, key: str, value: Any):
        cls._global[key] = value

    @classmethod
    def set_tenant(cls, tenant_id: str, key: str, value: Any):
        cls._tenant.setdefault(tenant_id, {})[key] = value

    @classmethod
    def set_environment(cls, env: str, key: str, value: Any):
        cls._env.setdefault(env, {})[key] = value

    @classmethod
    def set_override(cls, key: str, value: Any):
        cls._overrides[key] = value

    @classmethod
    def get(cls, key: str, tenant_id: str = "", env: str = "") -> Any:
        """Resolve value with override chain (most specific wins)."""
        # Runtime override (highest priority)
        if key in cls._overrides:
            return cls._overrides[key]

        # Environment
        if env and env in cls._env and key in cls._env[env]:
            return cls._env[env][key]

        # Tenant
        if tenant_id and tenant_id in cls._tenant and key in cls._tenant[tenant_id]:
            return cls._tenant[tenant_id][key]

        # Global (lowest priority)
        return cls._global.get(key)
