from typing import Dict, Any


class ChaosEngine:
    """Injects simulated failures to test system resilience."""

    _active_failures: Dict[str, bool] = {
        "LLM_FAILURE": False,
        "DB_TIMEOUT": False,
        "GPU_CRASH": False
    }

    @classmethod
    def inject_failure(cls, failure_type: str) -> bool:
        if failure_type in cls._active_failures:
            cls._active_failures[failure_type] = True
            return True
        return False

    @classmethod
    def resolve_failure(cls, failure_type: str) -> bool:
        if failure_type in cls._active_failures:
            cls._active_failures[failure_type] = False
            return True
        return False

    @classmethod
    def get_status(cls) -> Dict[str, bool]:
        return cls._active_failures

    @classmethod
    def _reset(cls):
        for k in cls._active_failures:
            cls._active_failures[k] = False
