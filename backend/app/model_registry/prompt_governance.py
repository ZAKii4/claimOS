from typing import Dict, Any, List
import uuid


class PromptGovernanceManager:
    """Manages the lifecycle and audit of AI Prompts."""

    _prompts: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register_prompt(cls, content: str, owner: str) -> Dict[str, Any]:
        p_id = str(uuid.uuid4())
        prompt = {
            "id": p_id,
            "version": "1.0",
            "content": content,
            "owner": owner,
            "status": "APPROVED",
            "risk_score": "LOW"
        }
        cls._prompts[p_id] = prompt
        return prompt

    @classmethod
    def get_prompt(cls, prompt_id: str) -> Dict[str, Any]:
        return cls._prompts.get(prompt_id, {})

    @classmethod
    def get_all(cls) -> List[Dict[str, Any]]:
        return list(cls._prompts.values())

    @classmethod
    def _reset(cls):
        cls._prompts.clear()
