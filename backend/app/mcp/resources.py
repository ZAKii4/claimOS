from pydantic import BaseModel
from typing import List, Dict, Optional, Any


class MCPResource(BaseModel):
    uri: str
    name: str
    mime_type: str
    description: str
    server_id: str


class ResourceManager:
    """Manages MCP Resources exposed by servers."""

    _mock_resources = [
        MCPResource(uri="file:///var/logs/app.log", name="Application Logs", mime_type="text/plain", description="System logs", server_id="mcp-filesystem"),
        MCPResource(uri="sql://main/users", name="Users Table", mime_type="application/json", description="List of users", server_id="mcp-sqlite")
    ]

    @classmethod
    def list_resources(cls, server_id: Optional[str] = None) -> List[MCPResource]:
        """Lists available resources."""
        if server_id:
            return [r for r in cls._mock_resources if r.server_id == server_id]
        return cls._mock_resources

    @classmethod
    def read_resource(cls, uri: str) -> Dict[str, Any]:
        """Simulates reading an MCP resource."""
        resource = next((r for r in cls._mock_resources if r.uri == uri), None)
        if not resource:
            return {"status": "ERROR", "message": "Resource not found"}
            
        return {
            "status": "SUCCESS",
            "uri": uri,
            "content": f"Mock content for {uri}",
            "mime_type": resource.mime_type
        }
