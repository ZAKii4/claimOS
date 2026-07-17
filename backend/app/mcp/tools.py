from pydantic import BaseModel
from typing import List, Dict, Optional, Any


class MCPTool(BaseModel):
    name: str
    description: str
    server_id: str
    input_schema: dict


class ToolDiscoveryEngine:
    """Discovers tools exposed by MCP servers."""

    _mock_tools = [
        MCPTool(name="read_file", description="Reads file content", server_id="mcp-filesystem", input_schema={"type": "object", "properties": {"path": {"type": "string"}}}),
        MCPTool(name="write_file", description="Writes file content", server_id="mcp-filesystem", input_schema={"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}}),
        MCPTool(name="query_db", description="Executes SQL query", server_id="mcp-sqlite", input_schema={"type": "object", "properties": {"query": {"type": "string"}}}),
        MCPTool(name="fetch_issue", description="Fetches a GitHub issue", server_id="mcp-github", input_schema={"type": "object", "properties": {"issue_number": {"type": "integer"}}})
    ]

    @classmethod
    def list_tools(cls, server_id: Optional[str] = None) -> List[MCPTool]:
        """Returns discovered tools, optionally filtered by server."""
        if server_id:
            return [t for t in cls._mock_tools if t.server_id == server_id]
        return cls._mock_tools

    @classmethod
    def invoke_tool(cls, name: str, args: dict) -> Dict[str, Any]:
        """Simulates invoking an MCP tool."""
        tool = next((t for t in cls._mock_tools if t.name == name), None)
        if not tool:
            return {"status": "ERROR", "message": "Tool not found"}
            
        return {
            "status": "SUCCESS",
            "tool": name,
            "result": f"Executed via {tool.server_id} with {args}"
        }
