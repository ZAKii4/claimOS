from typing import Dict, Optional
from app.platform.tenant.models import Tenant, TenantContext


class TenantResolver:
    """Resolves tenant from request context (JWT, API Key, Header, Subdomain)."""

    _tenants: Dict[str, Tenant] = {}
    _api_keys: Dict[str, str] = {}  # api_key -> tenant_id

    @classmethod
    def register_tenant(cls, tenant: Tenant):
        cls._tenants[tenant.id] = tenant

    @classmethod
    def register_api_key(cls, api_key: str, tenant_id: str):
        cls._api_keys[api_key] = tenant_id

    @classmethod
    def get_tenant(cls, tenant_id: str) -> Optional[Tenant]:
        return cls._tenants.get(tenant_id)

    @classmethod
    def get_all_tenants(cls):
        return list(cls._tenants.values())

    @classmethod
    def resolve_from_header(cls, tenant_id: str) -> Optional[TenantContext]:
        tenant = cls._tenants.get(tenant_id)
        if not tenant or not tenant.active:
            return None
        return TenantContext(tenant_id=tenant.id)

    @classmethod
    def resolve_from_api_key(cls, api_key: str) -> Optional[TenantContext]:
        tenant_id = cls._api_keys.get(api_key)
        if not tenant_id:
            return None
        return cls.resolve_from_header(tenant_id)

    @classmethod
    def resolve_from_subdomain(cls, subdomain: str) -> Optional[TenantContext]:
        for tenant in cls._tenants.values():
            if tenant.slug == subdomain and tenant.active:
                return TenantContext(tenant_id=tenant.id)
        return None
