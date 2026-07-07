from app.workflows.nodes.base import BaseNode


class ExclusiveGateway(BaseNode):
    type: str = "ExclusiveGateway"
    # Logic for XOR is handled by the Executor evaluating Edge conditions


class ParallelGateway(BaseNode):
    type: str = "ParallelGateway"
    # Logic for AND Fork/Join is handled by the Executor 
