from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class MCPServerProfile(BaseModel):
    id: str
    name: str
    version: str
    author: str
    description: str
    capabilities: List[str]
    allowed_tenants: List[str]
    is_active: bool = True


class MCPRegistry:
    """Central registry of discovered MCP servers."""

    _servers: Dict[str, MCPServerProfile] = {
        "mcp-filesystem": MCPServerProfile(
            id="mcp-filesystem", name="Filesystem Server", version="1.0", author="claimOS",
            description="Access local filesystem securely.", capabilities=["tools", "resources"],
            allowed_tenants=["*"]
        ),
        "mcp-github": MCPServerProfile(
            id="mcp-github", name="GitHub Server", version="1.1", author="ThirdParty",
            description="GitHub integration.", capabilities=["tools"],
            allowed_tenants=["tenant_1"]
        ),
        "mcp-sqlite": MCPServerProfile(
            id="mcp-sqlite", name="SQLite Server", version="2.0", author="claimOS",
            description="Database query server.", capabilities=["tools", "resources", "prompts"],
            allowed_tenants=["*"]
        ),
        "mcp-browser": MCPServerProfile(
            id="mcp-browser", name="Browser Server", version="1.0", author="Puppeteer",
            description="Headless browser access.", capabilities=["tools"],
            allowed_tenants=["tenant_2"], is_active=False
        )
    }

    @classmethod
    def list_servers(cls) -> List[MCPServerProfile]:
        return list(cls._servers.values())

    @classmethod
    def get_server(cls, server_id: str) -> Optional[MCPServerProfile]:
        return cls._servers.get(server_id)

    @classmethod
    def register_server(cls, profile: MCPServerProfile):
        cls._servers[profile.id] = profile

    @classmethod
    def set_status(cls, server_id: str, is_active: bool):
        if server_id in cls._servers:
            cls._servers[server_id].is_active = is_active

    @classmethod
    def _reset(cls):
        # Keeps initial state for testing
        cls._servers["mcp-browser"].is_active = False
