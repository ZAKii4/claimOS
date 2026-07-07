import asyncio
from typing import Dict, List, Callable, Awaitable
from app.agents.events import AgentEvent, AgentMessage


class EventBus:
    """
    In-memory async EventBus for agents to communicate via pub/sub.
    """
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[AgentEvent], Awaitable[None]]]] = {}
        self._message_queues: Dict[str, asyncio.Queue] = {}

    async def publish(self, event: AgentEvent):
        """Publish an event to all subscribers of this event_type."""
        if event.event_type in self._subscribers:
            for callback in self._subscribers[event.event_type]:
                asyncio.create_task(callback(event))

    def subscribe(self, event_type: str, callback: Callable[[AgentEvent], Awaitable[None]]):
        """Subscribe to an event_type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    async def send_message(self, message: AgentMessage):
        """Send a direct message to a specific agent's queue."""
        if message.target_id:
            if message.target_id not in self._message_queues:
                self._message_queues[message.target_id] = asyncio.Queue()
            await self._message_queues[message.target_id].put(message)
            
    async def get_messages(self, agent_id: str) -> List[AgentMessage]:
        """Fetch all pending messages for an agent."""
        if agent_id not in self._message_queues:
            return []
            
        messages = []
        queue = self._message_queues[agent_id]
        while not queue.empty():
            messages.append(await queue.get())
        return messages
