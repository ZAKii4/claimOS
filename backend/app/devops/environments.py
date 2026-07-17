from typing import Dict, Any, List


class EnvironmentManager:
    """Manages isolated configurations for various deployment environments."""

    _environments: Dict[str, Dict[str, Any]] = {
        "local": {"url": "http://localhost", "feature_flags": {"beta": True}},
        "development": {"url": "https://dev.claimos.com", "feature_flags": {"beta": True}},
        "staging": {"url": "https://staging.claimos.com", "feature_flags": {"beta": False}},
        "production": {"url": "https://claimos.com", "feature_flags": {"beta": False}},
    }

    @classmethod
    def get_environments(cls) -> List[Dict[str, Any]]:
        return [{"name": name, **config} for name, config in cls._environments.items()]

    @classmethod
    def get_environment(cls, name: str) -> Dict[str, Any]:
        return cls._environments.get(name, {})

    @classmethod
    def update_environment(cls, name: str, config: Dict[str, Any]) -> bool:
        if name in cls._environments:
            cls._environments[name].update(config)
            return True
        return False

    @classmethod
    def _reset(cls):
        # Reset to defaults
        pass
