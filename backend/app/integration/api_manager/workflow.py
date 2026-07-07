from typing import Dict, Any
from app.integration.api_manager.client import APIIntegrationManager
from app.integration.connectors.manager import ConnectorFramework


class ExternalWorkflowStep:
    """Represents a BPM workflow step that calls an external service."""

    @classmethod
    def execute(
        cls, 
        tenant_id: str, 
        connector_id: str, 
        endpoint: str, 
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an external call as part of a workflow."""
        connector = ConnectorFramework.get(connector_id)
        if not connector or not ConnectorFramework.is_active_for_tenant(tenant_id, connector_id):
            raise ValueError(f"Connector {connector_id} not available for tenant.")

        def _call_connector():
            return connector.send(endpoint, payload)

        # Wrap in API Integration Manager for resilience
        return APIIntegrationManager.execute(
            endpoint=endpoint,
            method=_call_connector,
            retries=2
        )
