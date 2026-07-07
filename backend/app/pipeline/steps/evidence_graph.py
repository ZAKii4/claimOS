from app.engines.base import EngineContext, EngineStatus
from app.engines.evidence_graph.manager import EvidenceGraphEngine


class EvidenceGraphStep:
    """
    Pipeline step that takes Extraction results,
    runs the Enterprise Evidence Graph Engine, 
    and updates the DocumentContext with the Knowledge Graph.
    """
    
    def __init__(self):
        self.engine = EvidenceGraphEngine()
        
    def execute(self, context: dict) -> dict:
        """
        Executes the Evidence Graph step on the provided pipeline context.
        """
        engine_context = EngineContext(
            claim_id=context.get("claim_id", "00000000-0000-0000-0000-000000000000"),
            input_data={
                "extraction_result": context.get("extraction_result")
            }
        )
        
        result = self.engine.process(engine_context)
        
        if result.status == EngineStatus.SUCCESS:
            context["evidence_graph_result"] = result.output_data.get("evidence_graph_result")
            context["evidence_graph_mermaid"] = result.output_data.get("evidence_graph_mermaid")
        else:
            context["evidence_graph_result"] = None
            context["evidence_graph_errors"] = result.errors
            
        return context
