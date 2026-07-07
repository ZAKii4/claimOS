from typing import Dict, Any, Optional
from app.agentic_ai.core.registry import AgentRegistry


class LocalToolEngine:
    """Manages local tool calling capabilities for Ollama models."""

    _available_tools = [
        "Python Engine", "Knowledge Platform", "Hybrid RAG", "Evidence Graph",
        "Validation Engine", "Decision Engine", "Simulation Engine", "Workflow Engine", "Analytics Engine",
        "Pipeline", "Analytics", "Simulation"
    ]

    @classmethod
    def invoke_tool(cls, agent_name: str, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Simulates an agent calling a local platform tool."""
        agent = AgentRegistry.get_agent(agent_name)
        if not agent:
            return {"status": "ERROR", "message": f"Agent {agent_name} not found"}
            
        if tool_name not in cls._available_tools:
            return {"status": "ERROR", "message": f"Tool {tool_name} is not registered in claimOS"}
            
        if tool_name not in agent.allowed_tools and "All" not in agent.allowed_tools:
            return {"status": "ERROR", "message": f"Agent {agent_name} is not allowed to use {tool_name}"}
            
        # Simulate local tool execution
        return {
            "status": "SUCCESS",
            "tool": tool_name,
            "result": f"Simulated output of {tool_name} with params {parameters}"
        }
