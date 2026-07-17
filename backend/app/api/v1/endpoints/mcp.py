from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from pydantic import BaseModel

from app.mcp.registry import MCPRegistry, MCPServerProfile
from app.mcp.transport import TransportManager
from app.mcp.capabilities import CapabilityResolver
from app.mcp.tools import ToolDiscoveryEngine, MCPTool
from app.mcp.resources import ResourceManager, MCPResource
from app.mcp.prompts import PromptExchangeManager, MCPPrompt
from app.mcp.sessions import MCPSessionManager, MCPSession
from app.mcp.security import MCPSecurityManager

router = APIRouter(prefix="/mcp", tags=["Enterprise MCP Ecosystem"])


class ConnectRequest(BaseModel):
    server_id: str
    transport_type: str


class InvokeToolRequest(BaseModel):
    tool_name: str
    args: dict


class SessionRequest(BaseModel):
    server_id: str


@router.get("/servers", response_model=List[MCPServerProfile])
def list_servers():
    """Lists registered MCP servers."""
    return MCPRegistry.list_servers()


@router.post("/servers/register")
def register_server(profile: MCPServerProfile):
    """Registers a new MCP server."""
    MCPRegistry.register_server(profile)
    return {"status": "Registered"}


@router.get("/tools", response_model=List[MCPTool])
def list_tools(server_id: str = None):
    """Lists discovered MCP tools."""
    return ToolDiscoveryEngine.list_tools(server_id)


@router.get("/resources", response_model=List[MCPResource])
def list_resources(server_id: str = None):
    """Lists available MCP resources."""
    return ResourceManager.list_resources(server_id)


@router.get("/prompts", response_model=List[MCPPrompt])
def list_prompts(server_id: str = None):
    """Lists available MCP prompts."""
    return PromptExchangeManager.list_prompts(server_id)


@router.post("/sessions", response_model=MCPSession)
def open_session(req: SessionRequest):
    """Opens a new MCP session."""
    return MCPSessionManager.create_session(req.server_id)


@router.post("/sessions/{session_id}/resume")
def resume_session(session_id: str):
    """Resumes an inactive MCP session."""
    res = MCPSessionManager.resume_session(session_id)
    if res["status"] == "ERROR":
        raise HTTPException(status_code=404, detail=res["message"])
    return res


@router.get("/capabilities/{server_id}")
def get_capabilities(server_id: str):
    """Negotiates capabilities with an MCP server."""
    res = CapabilityResolver.resolve_capabilities(server_id)
    if res["status"] == "ERROR":
        raise HTTPException(status_code=404, detail=res["message"])
    return res


@router.get("/marketplace")
def list_marketplace():
    """Mocks marketplace packages."""
    return [{"id": "mcp-jira", "name": "Jira MCP Server", "verified": True}]


@router.post("/marketplace/install")
def install_package(server_id: str):
    """Simulates secure installation of an MCP package."""
    return {"status": "Installed", "server_id": server_id}
