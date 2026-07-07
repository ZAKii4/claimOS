from typing import Dict, Any, List, Optional


class TenantResourceStore:
    """
    Tenant-isolated resource store.
    All data is scoped by tenant_id. Cross-tenant access is structurally impossible.
    """

    _store: Dict[str, Dict[str, List[Any]]] = {}  # tenant_id -> resource_type -> items

    @classmethod
    def store(cls, tenant_id: str, resource_type: str, item: Any):
        cls._store.setdefault(tenant_id, {}).setdefault(resource_type, []).append(item)

    @classmethod
    def get(cls, tenant_id: str, resource_type: str) -> List[Any]:
        return cls._store.get(tenant_id, {}).get(resource_type, [])

    @classmethod
    def get_all_for_tenant(cls, tenant_id: str) -> Dict[str, List[Any]]:
        return cls._store.get(tenant_id, {})

    @classmethod
    def clear_tenant(cls, tenant_id: str):
        cls._store.pop(tenant_id, None)
