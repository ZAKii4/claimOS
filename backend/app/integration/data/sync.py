import uuid
from typing import Dict, Any, List
from app.integration.core.models import SyncResult
from app.integration.connectors.manager import ConnectorFramework


class SynchronizationEngine:
    """Handles synchronization of data between claimOS and external systems."""

    _sync_history: List[SyncResult] = []
    
    @classmethod
    def sync_to_external(
        cls, 
        tenant_id: str, 
        connector_id: str, 
        endpoint: str, 
        data: List[Dict[str, Any]]
    ) -> SyncResult:
        connector = ConnectorFramework.get(connector_id)
        
        result = SyncResult(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            connector_id=connector_id,
        )
        
        if not connector or not ConnectorFramework.is_active_for_tenant(tenant_id, connector_id):
            result.status = "FAILED"
            result.details = f"Connector {connector_id} not active or not found."
            cls._sync_history.append(result)
            return result

        # Ensure connection
        if not connector.connect():
            result.status = "FAILED"
            result.details = "Connection failed."
            cls._sync_history.append(result)
            return result

        # Simulate syncing records
        success_count = 0
        conflict_count = 0
        
        for record in data:
            try:
                # Basic idempotency check simulation
                response = connector.send(endpoint, record)
                if response.get("status") == "conflict":
                    conflict_count += 1
                else:
                    success_count += 1
            except Exception:
                conflict_count += 1

        result.records_synced = success_count
        result.conflicts = conflict_count
        result.status = "SUCCESS" if conflict_count == 0 else "PARTIAL"
        
        cls._sync_history.append(result)
        return result

    @classmethod
    def get_history(cls, tenant_id: str = None) -> List[SyncResult]:
        if tenant_id:
            return [s for s in cls._sync_history if s.tenant_id == tenant_id]
        return list(cls._sync_history)
