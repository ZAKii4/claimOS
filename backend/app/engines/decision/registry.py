import pkgutil
import inspect
import importlib

from app.engines.decision.base_strategy import BaseDecisionStrategy


class StrategyRegistry:
    """
    Auto-discovers and maintains a list of all active Decision Strategies.
    """
    
    def __init__(self):
        self._strategies: list[BaseDecisionStrategy] = []

    def discover_strategies(self, package_name: str = "app.engines.decision.strategies") -> None:
        """
        Dynamically imports all modules within the given package and instantiates 
        concrete subclasses of BaseDecisionStrategy.
        """
        self._strategies.clear()
        package = importlib.import_module(package_name)
        
        for _, module_name, is_pkg in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
            if not is_pkg:
                module = importlib.import_module(module_name)
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseDecisionStrategy) and obj is not BaseDecisionStrategy:
                        if not getattr(obj, "__abstractmethods__", None):
                            self.register(obj())
                            
        # Sort by priority descending right after discovery
        self._strategies.sort(key=lambda s: s.priority, reverse=True)

    def register(self, strategy: BaseDecisionStrategy) -> None:
        self._strategies.append(strategy)

    def get_strategies(self) -> list[BaseDecisionStrategy]:
        return self._strategies
