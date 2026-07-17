from typing import Dict, Any, List


class RunbookManager:
    """Manages operational playbooks for incident recovery and routine maintenance."""

    _runbooks: List[Dict[str, Any]] = []

    @classmethod
    def create_runbook(cls, title: str, steps: List[str]) -> Dict[str, Any]:
        rb = {
            "id": f"rb-{len(cls._runbooks)+1}",
            "title": title,
            "steps": steps,
            "version": "1.0"
        }
        cls._runbooks.append(rb)
        return rb

    @classmethod
    def get_runbooks(cls) -> List[Dict[str, Any]]:
        return cls._runbooks

    @classmethod
    def _reset(cls):
        cls._runbooks.clear()
