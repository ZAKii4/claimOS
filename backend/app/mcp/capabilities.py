from typing import Dict, Any, Optional
from app.mcp.registry import MCPRegistry


class CapabilityResolver:
    """Negotiates capabilities with an MCP Server."""

    @classmethod
    def resolve_capabilities(cls, server_id: str) -> Dict[str, Any]:
        """Simulates MCP initialization and capabilities negotiation."""
        server = MCPRegistry.get_server(server_id)
        if not server or not server.is_active:
            return {"status": "ERROR", "message": "Server unavailable"}
            
        return {
            "status": "SUCCESS",
            "server": server.name,
            "capabilities": {
                "tools": "tools" in server.capabilities,
                "resources": "resources" in server.capabilities,
                "prompts": "prompts" in server.capabilities
            },
            "mcp_version": "2024-11-05"
        }
