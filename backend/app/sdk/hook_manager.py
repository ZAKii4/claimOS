from typing import Dict, Any, List, Callable

class HookManager:
    """Enterprise Hook System for intercepting core pipelines."""

    _hooks: Dict[str, List[str]] = {
        "Before Pipeline": [],
        "After Pipeline": [],
        "Before OCR": [],
        "After OCR": [],
        "Before Decision": [],
        "After Decision": [],
        "Before Agent": [],
        "After Agent": [],
        "Before LLM": [],
        "After LLM": [],
        "Before Workflow": [],
        "After Workflow": []
    }

    @classmethod
    def register_hook(cls, hook_name: str, plugin_id: str) -> bool:
        if hook_name in cls._hooks:
            cls._hooks[hook_name].append(plugin_id)
            return True
        return False

    @classmethod
    def get_hooks(cls) -> Dict[str, List[str]]:
        return cls._hooks

    @classmethod
    def _reset(cls):
        for k in cls._hooks:
            cls._hooks[k] = []
