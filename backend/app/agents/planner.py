from typing import List, Dict
from pydantic import BaseModel
from app.agents.context import AgentContext
from app.agents.base import BaseAgent


class ExecutionNode(BaseModel):
    agent_id: str
    dependencies: List[str] = []


class ExecutionGraph(BaseModel):
    nodes: List[ExecutionNode]


class Planner:
    """
    Determines which agents should run for a given context and creates an ExecutionGraph.
    """
    
    def __init__(self, registry):
        self.registry = registry
        
    async def create_plan(self, context: AgentContext) -> ExecutionGraph:
        """
        MVP Planner: creates a static sequential/parallel plan.
        In the future, this can use a LLM or rules engine to build dynamic graphs.
        """
        available_agents = self.registry.get_all()
        
        # Hardcoded MVP DAG for claim processing
        nodes = []
        
        # 1. OCR (No deps)
        if "ocr_supervisor" in available_agents:
            nodes.append(ExecutionNode(agent_id="ocr_supervisor", dependencies=[]))
            
        # 2. Classification & Fraud can run in parallel after OCR
        if "classification_supervisor" in available_agents:
            nodes.append(ExecutionNode(agent_id="classification_supervisor", dependencies=["ocr_supervisor"]))
            
        if "fraud_agent" in available_agents:
            nodes.append(ExecutionNode(agent_id="fraud_agent", dependencies=["ocr_supervisor"]))
            
        # 3. Validation depends on Classification
        if "validation_supervisor" in available_agents:
            nodes.append(ExecutionNode(agent_id="validation_supervisor", dependencies=["classification_supervisor"]))
            
        return ExecutionGraph(nodes=nodes)
