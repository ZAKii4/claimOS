from typing import Dict, Any, List
from pydantic import BaseModel, Field
import uuid


class PromptVariant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    template: str
    version: str
    scores: List[float] = Field(default_factory=list)

    @property
    def avg_score(self) -> float:
        if not self.scores:
            return 0.0
        return sum(self.scores) / len(self.scores)


class PromptOptimizer:
    """Manages A/B testing and automatic optimization of LLM prompts."""

    _prompts: Dict[str, List[PromptVariant]] = {}

    @classmethod
    def register_variant(cls, task_name: str, template: str, version: str) -> PromptVariant:
        if task_name not in cls._prompts:
            cls._prompts[task_name] = []
        variant = PromptVariant(template=template, version=version)
        cls._prompts[task_name].append(variant)
        return variant

    @classmethod
    def record_feedback(cls, task_name: str, version: str, score: float):
        variants = cls._prompts.get(task_name, [])
        for v in variants:
            if v.version == version:
                v.scores.append(score)
                break

    @classmethod
    def get_best_variant(cls, task_name: str) -> PromptVariant:
        variants = cls._prompts.get(task_name, [])
        if not variants:
            raise ValueError(f"No prompt variants for task {task_name}")
        return sorted(variants, key=lambda v: v.avg_score, reverse=True)[0]

    @classmethod
    def evaluate_multiple(cls, tenant_id: str, task_name: str, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulates evaluating all variants for a task and returns the winner."""
        variants = cls._prompts.get(task_name, [])
        if not variants:
            return {}

        # Simulating random-ish scores for evaluation based on version string length just for test determinism
        results = {}
        for v in variants:
            mock_score = 50.0 + len(v.version) * 5.0
            cls.record_feedback(task_name, v.version, mock_score)
            results[v.version] = mock_score
            
        winner = cls.get_best_variant(task_name)
        return {
            "winner_version": winner.version,
            "results": results
        }

    @classmethod
    def _clear_all(cls):
        cls._prompts.clear()
