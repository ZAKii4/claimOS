import uuid
from typing import List, Dict, Any, Optional
from app.workflows.models import WorkflowDefinition, WorkflowEdge
from app.workflows.nodes.base import BaseNode
from app.workflows.nodes.tasks import ServiceTask, HumanTask
from app.workflows.nodes.gateways import ExclusiveGateway, ParallelGateway


class WorkflowBuilder:
    """Fluent API for constructing DAG workflows programmatically."""
    
    def __init__(self, name: str):
        self.def_id = str(uuid.uuid4())
        self.name = name
        self.nodes: List[BaseNode] = []
        self.edges: List[WorkflowEdge] = []
        self.start_node_id: Optional[str] = None
        
        self._current_node_id: Optional[str] = None
        self._gateway_id: Optional[str] = None  # Tracks active gateway for condition/path
        
    def start(self, node: BaseNode) -> 'WorkflowBuilder':
        self.start_node_id = node.id
        self._register_node(node)
        self._current_node_id = node.id
        return self
        
    def then(self, node: BaseNode) -> 'WorkflowBuilder':
        if not self._current_node_id:
            raise ValueError("Workflow must be started first")
        
        self._register_node(node)
        self.edges.append(WorkflowEdge(source_id=self._current_node_id, target_id=node.id))
        self._current_node_id = node.id
        self._gateway_id = None  # Exiting gateway mode
        return self
        
    def branch(self, gateway: ExclusiveGateway) -> 'WorkflowBuilder':
        """Starts an Exclusive (XOR) Gateway."""
        self.then(gateway)
        self._gateway_id = gateway.id
        return self
        
    def condition(self, target_node: BaseNode, expression: str) -> 'WorkflowBuilder':
        """Adds a conditional edge from the current gateway to the target node."""
        gw_id = self._gateway_id or self._current_node_id
        self._register_node(target_node)
        self.edges.append(WorkflowEdge(
            source_id=gw_id,
            target_id=target_node.id,
            condition_expression=expression
        ))
        # Keep _current_node_id on the gateway so multiple conditions can be added
        return self
        
    def parallel(self, gateway: ParallelGateway) -> 'WorkflowBuilder':
        """Starts a Parallel (AND) Gateway."""
        self.then(gateway)
        self._gateway_id = gateway.id
        return self
        
    def path(self, target_node: BaseNode) -> 'WorkflowBuilder':
        """Adds a parallel path from the current gateway."""
        gw_id = self._gateway_id or self._current_node_id
        self._register_node(target_node)
        self.edges.append(WorkflowEdge(
            source_id=gw_id,
            target_id=target_node.id
        ))
        return self

    def end(self) -> WorkflowDefinition:
        return WorkflowDefinition(
            id=self.def_id,
            name=self.name,
            nodes=self.nodes,
            edges=self.edges,
            start_node_id=self.start_node_id
        )
        
    def _register_node(self, node: BaseNode):
        """Adds a node to the definition if not already present. Does NOT move the cursor."""
        if not any(n.id == node.id for n in self.nodes):
            self.nodes.append(node)
