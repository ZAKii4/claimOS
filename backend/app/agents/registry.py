import importlib
import pkgutil
import inspect
from typing import Dict, Type
from app.agents.base import BaseAgent


class AgentRegistry:
    """Auto-discovers and registers all BaseAgent subclasses in app/agents/modules/"""
    
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        
    def discover(self):
        """Dynamically imports and instantiates all agents."""
        try:
            import app.agents.modules as modules_pkg
        except ImportError:
            return
            
        for _, module_name, _ in pkgutil.iter_modules(modules_pkg.__path__):
            full_module_name = f"app.agents.modules.{module_name}"
            module = importlib.import_module(full_module_name)
            
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, BaseAgent) and obj is not BaseAgent:
                    # Instantiate and register
                    instance = obj()
                    self._agents[instance.id] = instance
                    
    def get_agent(self, agent_id: str) -> BaseAgent:
        return self._agents.get(agent_id)
        
    def get_all(self) -> Dict[str, BaseAgent]:
        return self._agents
