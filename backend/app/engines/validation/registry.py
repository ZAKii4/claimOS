import pkgutil
import inspect
import importlib

from app.engines.validation.base_rule import ValidationRule


class RuleRegistry:
    """
    Auto-discovers and maintains a list of all active ValidationRules.
    """
    
    def __init__(self):
        self._rules: list[ValidationRule] = []

    def discover_rules(self, package_name: str = "app.engines.validation.validators") -> None:
        """
        Dynamically imports all modules within the given package and instantiates 
        concrete subclasses of ValidationRule.
        """
        self._rules.clear()
        package = importlib.import_module(package_name)
        
        for _, module_name, is_pkg in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
            if not is_pkg:
                module = importlib.import_module(module_name)
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Check if it's a subclass of ValidationRule and NOT the base class itself
                    if issubclass(obj, ValidationRule) and obj is not ValidationRule:
                        # Ensure it's not an abstract class by checking if it has unimplemented abstract methods
                        if not getattr(obj, "__abstractmethods__", None):
                            self.register(obj())

    def register(self, rule: ValidationRule) -> None:
        self._rules.append(rule)

    def get_all_rules(self) -> list[ValidationRule]:
        return self._rules
