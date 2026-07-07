from typing import Dict, List, Optional
from app.integration.connectors.base import Connector


class ConnectorFramework:
    """Auto-discovery and management of connectors."""

    _connectors: Dict[str, Connector] = {}
    _tenant_activations: Dict[str, List[str]] = {}  # tenant_id -> list of connector_ids

    @classmethod
    def register(cls, connector: Connector):
        cls._connectors[connector.id] = connector

    @classmethod
    def get(cls, connector_id: str) -> Optional[Connector]:
        return cls._connectors.get(connector_id)

    @classmethod
    def get_all(cls) -> List[Connector]:
        return list(cls._connectors.values())

    @classmethod
    def activate_for_tenant(cls, tenant_id: str, connector_id: str):
        if connector_id in cls._connectors:
            cls._tenant_activations.setdefault(tenant_id, []).append(connector_id)

    @classmethod
    def is_active_for_tenant(cls, tenant_id: str, connector_id: str) -> bool:
        return connector_id in cls._tenant_activations.get(tenant_id, [])

    @classmethod
    def get_active_for_tenant(cls, tenant_id: str) -> List[Connector]:
        active_ids = cls._tenant_activations.get(tenant_id, [])
        return [cls._connectors[cid] for cid in active_ids if cid in cls._connectors]
