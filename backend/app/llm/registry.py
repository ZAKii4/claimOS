import importlib
import pkgutil
import inspect
from typing import Dict, Type
from app.llm.base import BaseLLMProvider


class ProviderRegistry:
    """Auto-discovers and registers all BaseLLMProvider subclasses in app/llm/providers/"""
    
    def __init__(self):
        self._providers: Dict[str, BaseLLMProvider] = {}
        
    def discover(self):
        """Dynamically imports and instantiates all providers."""
        try:
            import app.llm.providers as providers_pkg
        except ImportError:
            return
            
        for _, module_name, _ in pkgutil.iter_modules(providers_pkg.__path__):
            full_module_name = f"app.llm.providers.{module_name}"
            module = importlib.import_module(full_module_name)
            
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, BaseLLMProvider) and obj is not BaseLLMProvider:
                    instance = obj()
                    self._providers[instance.name] = instance
                    
    def get_provider(self, name: str) -> BaseLLMProvider:
        return self._providers.get(name)
        
    def get_all(self) -> Dict[str, BaseLLMProvider]:
        return self._providers
