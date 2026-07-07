import uuid
from datetime import datetime
from typing import Dict, List, Optional
from app.platform.tenant.models import WorkerNode, NodeStatus


class NodeManager:
    """Cluster management with worker registration, heartbeat, and leader election."""

    _nodes: Dict[str, WorkerNode] = {}
    _leader_id: Optional[str] = None

    @classmethod
    def register(cls, host: str, port: int = 8000) -> WorkerNode:
        node = WorkerNode(id=str(uuid.uuid4()), host=host, port=port)
        cls._nodes[node.id] = node
        if not cls._leader_id:
            cls._elect_leader()
        return node

    @classmethod
    def heartbeat(cls, node_id: str, cpu: float = 0.0, memory: float = 0.0, tasks: int = 0):
        node = cls._nodes.get(node_id)
        if node:
            node.last_heartbeat = datetime.utcnow()
            node.cpu_usage = cpu
            node.memory_usage = memory
            node.task_count = tasks
            node.status = NodeStatus.ACTIVE

    @classmethod
    def mark_down(cls, node_id: str):
        node = cls._nodes.get(node_id)
        if node:
            node.status = NodeStatus.DOWN
            node.is_leader = False
            if cls._leader_id == node_id:
                cls._leader_id = None
                cls._elect_leader()

    @classmethod
    def get_leader(cls) -> Optional[WorkerNode]:
        if cls._leader_id:
            return cls._nodes.get(cls._leader_id)
        return None

    @classmethod
    def get_active_nodes(cls) -> List[WorkerNode]:
        return [n for n in cls._nodes.values() if n.status == NodeStatus.ACTIVE]

    @classmethod
    def get_all_nodes(cls) -> List[WorkerNode]:
        return list(cls._nodes.values())

    @classmethod
    def get_least_loaded(cls) -> Optional[WorkerNode]:
        active = cls.get_active_nodes()
        if not active:
            return None
        return min(active, key=lambda n: n.task_count)

    @classmethod
    def _elect_leader(cls):
        active = cls.get_active_nodes()
        if active:
            leader = active[0]
            leader.is_leader = True
            cls._leader_id = leader.id
