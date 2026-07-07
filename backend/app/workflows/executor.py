import asyncio
import time
from typing import Dict, List, Optional
from app.workflows.models import WorkflowInstance, WorkflowDefinition, WorkflowState, TaskState, WorkflowTaskExecution
from app.workflows.nodes.base import BaseNode
from app.workflows.nodes.gateways import ExclusiveGateway, ParallelGateway
from app.workflows.expressions import ExpressionEngine
from app.observability.decorators import traceable


class WorkflowExecutor:
    """DAG Traversal and execution engine."""
    
    def __init__(self, definition: WorkflowDefinition, instance: WorkflowInstance):
        self.definition = definition
        self.instance = instance
        self.nodes_by_id: Dict[str, BaseNode] = {n.id: n for n in definition.nodes}
        
    @traceable(name="WorkflowExecution")
    async def run(self):
        if self.instance.state not in [WorkflowState.PENDING, WorkflowState.SUSPENDED]:
            raise ValueError(f"Cannot run workflow in state {self.instance.state}")
            
        self.instance.state = WorkflowState.RUNNING
        self.instance.start_time = self.instance.start_time or time.time()
        
        # If starting fresh
        if not self.instance.current_node_ids:
            self.instance.current_node_ids = [self.definition.start_node_id]
            
        try:
            while self.instance.current_node_ids and self.instance.state == WorkflowState.RUNNING:
                next_nodes: List[str] = []
                
                # Execute current level concurrently (important for Parallel Gateways)
                tasks = [self._execute_node(nid) for nid in self.instance.current_node_ids]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Check for exceptions first
                for result in results:
                    if isinstance(result, Exception):
                        raise result
                
                # If workflow was suspended by a HumanTask, stop the loop
                if self.instance.state == WorkflowState.SUSPENDED:
                    break
                
                # Process results — calculate next nodes based on edges
                for nid in self.instance.current_node_ids:
                    out_edges = [e for e in self.definition.edges if e.source_id == nid]
                    node = self.nodes_by_id[nid]
                    
                    if isinstance(node, ExclusiveGateway):
                        # XOR: Find the first condition that matches
                        for edge in out_edges:
                            if ExpressionEngine.evaluate(
                                edge.condition_expression or "",
                                self.instance.context.variables
                            ):
                                next_nodes.append(edge.target_id)
                                break
                            
                    elif isinstance(node, ParallelGateway):
                        # AND: Take all outgoing edges
                        for edge in out_edges:
                            next_nodes.append(edge.target_id)
                            
                    else:
                        # Standard node: follow all unconditional edges
                        for edge in out_edges:
                            next_nodes.append(edge.target_id)
                            
                self.instance.current_node_ids = list(set(next_nodes))
                
            if not self.instance.current_node_ids and self.instance.state == WorkflowState.RUNNING:
                self.instance.state = WorkflowState.COMPLETED
                self.instance.end_time = time.time()
                
        except Exception as e:
            self.instance.state = WorkflowState.FAILED
            self.instance.error = str(e)
            self.instance.end_time = time.time()
            await self._compensate()
            
    async def _execute_node(self, node_id: str):
        node = self.nodes_by_id[node_id]
        
        # Gateways are routing-only; they don't execute business logic
        if isinstance(node, (ExclusiveGateway, ParallelGateway)):
            return
        
        task_id = f"task_{node_id}_{time.time()}"
        execution = WorkflowTaskExecution(
            node_id=node_id,
            task_id=task_id,
            start_time=time.time(),
            state=TaskState.RUNNING
        )
        self.instance.task_executions[task_id] = execution
        
        try:
            updates = await node.execute(self.instance.context)
            
            # Apply context updates
            if updates:
                for k, v in updates.items():
                    self.instance.context.set(k, v)
                    
            # Handle suspension (e.g. Human Task signals pending)
            if updates and updates.get(f"{node.id}_pending"):
                self.instance.state = WorkflowState.SUSPENDED
                execution.state = TaskState.PENDING
                return
                
            execution.state = TaskState.COMPLETED
            execution.end_time = time.time()
        except Exception as e:
            execution.state = TaskState.FAILED
            execution.error = str(e)
            execution.end_time = time.time()
            raise
            
    async def _compensate(self):
        """Runs compensation logic for completed tasks in reverse order."""
        completed_tasks = [
            t for t in self.instance.task_executions.values()
            if t.state == TaskState.COMPLETED
        ]
        completed_tasks.sort(key=lambda x: x.end_time or 0, reverse=True)
        
        for task in completed_tasks:
            node = self.nodes_by_id[task.node_id]
            try:
                await node.compensate(self.instance.context)
                task.state = TaskState.COMPENSATED
            except Exception:
                pass  # Log compensation failure but continue
