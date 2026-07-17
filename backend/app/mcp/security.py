from typing import Dict, Any
from app.mcp.registry import MCPRegistry


class MCPSecurityManager:
    """Secures MCP exchanges via RBAC and Tenant Isolation."""

    @classmethod
    def check_access(cls, server_id: str, tenant_id: str) -> Dict[str, Any]:
        """Validates if a tenant can access a specific server."""
        server = MCPRegistry.get_server(server_id)
        if not server:
            return {"status": "DENIED", "reason": "Server not found"}
            
        if "*" in server.allowed_tenants or tenant_id in server.allowed_tenants:
            return {"status": "GRANTED"}
            
        return {"status": "DENIED", "reason": "Tenant not authorized"}

    @classmethod
    def validate_tool_schema(cls, tool_name: str, args: dict) -> bool:
        """Simulates schema validation for security."""
        # Simple mock: if args has 'malicious', block it
        if "malicious" in str(args).lower():
            return False
        return True
