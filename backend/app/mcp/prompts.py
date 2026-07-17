from pydantic import BaseModel
from typing import List, Dict, Optional, Any


class MCPPrompt(BaseModel):
    name: str
    description: str
    arguments: List[dict]
    server_id: str


class PromptExchangeManager:
    """Manages Prompts exposed by MCP servers."""

    _mock_prompts = [
        MCPPrompt(
            name="analyze_query", description="Analyzes a SQL query", 
            arguments=[{"name": "query", "description": "The SQL query", "required": True}], 
            server_id="mcp-sqlite"
        )
    ]

    @classmethod
    def list_prompts(cls, server_id: Optional[str] = None) -> List[MCPPrompt]:
        """Lists available MCP prompts."""
        if server_id:
            return [p for p in cls._mock_prompts if p.server_id == server_id]
        return cls._mock_prompts

    @classmethod
    def get_prompt(cls, name: str, args: dict) -> Dict[str, Any]:
        """Simulates fetching an MCP prompt."""
        prompt = next((p for p in cls._mock_prompts if p.name == name), None)
        if not prompt:
            return {"status": "ERROR", "message": "Prompt not found"}
            
        return {
            "status": "SUCCESS",
            "name": name,
            "messages": [
                {
                    "role": "user",
                    "content": {"type": "text", "text": f"Simulated prompt {name} with args {args}"}
                }
            ]
        }
