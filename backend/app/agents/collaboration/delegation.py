from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import uuid
from enum import Enum


class TaskStatus(str, Enum):
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"


class DelegatedTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    delegator_id: str
    delegatee_id: str
    payload: Dict[str, Any]
    status: TaskStatus = TaskStatus.ASSIGNED
    timeout_seconds: int = 60
    retries: int = 0
    max_retries: int = 3
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class DelegationEngine:
    """Handles assignment of sub-tasks from one agent to another."""

    _tasks: Dict[str, DelegatedTask] = {}

    @classmethod
    def delegate(
        cls, 
        tenant_id: str, 
        delegator_id: str, 
        delegatee_id: str, 
        payload: Dict[str, Any],
        max_retries: int = 3
    ) -> DelegatedTask:
        task = DelegatedTask(
            tenant_id=tenant_id,
            delegator_id=delegator_id,
            delegatee_id=delegatee_id,
            payload=payload,
            max_retries=max_retries
        )
        cls._tasks[task.id] = task
        return task

    @classmethod
    def report_success(cls, task_id: str, result: Dict[str, Any]):
        task = cls._tasks.get(task_id)
        if task:
            task.status = TaskStatus.COMPLETED
            task.result = result

    @classmethod
    def report_failure(cls, task_id: str, error: str):
        task = cls._tasks.get(task_id)
        if task:
            if task.retries < task.max_retries:
                task.retries += 1
                task.status = TaskStatus.ASSIGNED  # Ready for retry
            else:
                task.status = TaskStatus.FAILED
                task.error = error

    @classmethod
    def get_task(cls, task_id: str) -> Optional[DelegatedTask]:
        return cls._tasks.get(task_id)

    @classmethod
    def _clear_all(cls):
        cls._tasks.clear()
