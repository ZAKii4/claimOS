import asyncio
from typing import Dict
from app.agents.planner import ExecutionGraph
from app.agents.context import AgentContext
from app.agents.memory import SharedMemory
from app.agents.base import AgentResult


class Scheduler:
    """
    Executes the ExecutionGraph asynchronously, respecting dependencies.
    """
    def __init__(self, registry):
        self.registry = registry

    async def execute_graph(self, graph: ExecutionGraph, context: AgentContext, memory: SharedMemory) -> Dict[str, AgentResult]:
        results = {}
        pending = {node.agent_id: node for node in graph.nodes}
        running_tasks = {}
        
        while pending or running_tasks:
            # Find nodes ready to run (all dependencies are in results)
            ready_to_run = []
            for agent_id, node in list(pending.items()):
                if all(dep in results for dep in node.dependencies):
                    ready_to_run.append(agent_id)
                    
            # Schedule them
            for agent_id in ready_to_run:
                del pending[agent_id]
                agent = self.registry.get_agent(agent_id)
                if agent:
                    # Run health check and plan
                    task = asyncio.create_task(self._run_agent(agent, context, memory))
                    running_tasks[agent_id] = task
                    
            if not running_tasks:
                # Deadlock detected or missing dependencies
                break
                
            # Wait for at least one task to finish
            done, _ = await asyncio.wait(running_tasks.values(), return_when=asyncio.FIRST_COMPLETED)
            
            for task in done:
                # Find which agent this task belonged to
                agent_id = next(aid for aid, t in running_tasks.items() if t == task)
                del running_tasks[agent_id]
                try:
                    results[agent_id] = task.result()
                except Exception as e:
                    print(f"Agent {agent_id} failed: {e}")
                    results[agent_id] = None # Or a failed AgentResult
                    
        return results

    async def _run_agent(self, agent, context, memory) -> AgentResult:
        if not agent.health_check():
            return None
        
        should_run = await agent.plan(context, memory)
        if not should_run:
            return None
            
        result = await agent.execute(context, memory)
        
        is_valid = await agent.validate(result)
        if not is_valid:
            await agent.rollback(context, memory)
            
        return result
