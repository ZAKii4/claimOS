from typing import Dict, Any
from app.agents.memory.memory import MemoryManager, MemoryType


class ReflectionEngine:
    """Enables agents to self-evaluate after a task."""

    @classmethod
    def evaluate(cls, tenant_id: str, agent_id: str, task_context_id: str, outcome: str, expected_outcome: str) -> Dict[str, Any]:
        """Calculates performance and extracts lessons."""
        
        success = (outcome == expected_outcome)
        
        evaluation = {
            "success": success,
            "error_detected": not success,
            "lesson": ""
        }

        if success:
            evaluation["lesson"] = "Execution matched expectations."
        else:
            evaluation["lesson"] = f"Expected {expected_outcome} but got {outcome}. Need to refine logic."
            
        # Store lesson in semantic memory
        MemoryManager.store(
            tenant_id=tenant_id,
            agent_id=agent_id,
            m_type=MemoryType.SEMANTIC,
            content=evaluation["lesson"],
            metadata={"source_context": task_context_id}
        )
        
        return evaluation
