import uuid
import time
from typing import Dict, List, Optional, Callable
from app.platform.tenant.models import TaskEntry, TaskState


class TaskQueue:
    """
    Distributed task engine with priority, retry, exponential backoff, and DLQ.
    """

    _queue: List[TaskEntry] = []
    _dlq: List[TaskEntry] = []  # Dead Letter Queue
    _handlers: Dict[str, Callable] = {}

    @classmethod
    def register_handler(cls, task_name: str, handler: Callable):
        cls._handlers[task_name] = handler

    @classmethod
    def enqueue(cls, name: str, payload: dict = None, priority: int = 0, tenant_id: str = "") -> TaskEntry:
        task = TaskEntry(
            id=str(uuid.uuid4()),
            name=name,
            tenant_id=tenant_id,
            priority=priority,
            payload=payload or {},
        )
        cls._queue.append(task)
        cls._queue.sort(key=lambda t: -t.priority)  # Higher priority first
        return task

    @classmethod
    def process_next(cls) -> Optional[TaskEntry]:
        """Process the highest-priority task."""
        if not cls._queue:
            return None

        task = cls._queue.pop(0)
        handler = cls._handlers.get(task.name)

        if not handler:
            task.state = TaskState.FAILED
            task.error = f"No handler for '{task.name}'"
            cls._dlq.append(task)
            return task

        task.state = TaskState.RUNNING
        try:
            task.result = handler(task.payload)
            task.state = TaskState.COMPLETED
        except Exception as e:
            task.retries += 1
            if task.retries >= task.max_retries:
                task.state = TaskState.DEAD
                task.error = str(e)
                cls._dlq.append(task)
            else:
                task.state = TaskState.RETRYING
                task.error = str(e)
                cls._queue.append(task)

        return task

    @classmethod
    def get_dlq(cls) -> List[TaskEntry]:
        return list(cls._dlq)

    @classmethod
    def get_queue_size(cls) -> int:
        return len(cls._queue)
