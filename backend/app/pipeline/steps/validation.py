from app.engines.base import EngineContext, EngineStatus
from app.engines.validation.manager import ValidationEngine


class ValidationStep:
    """
    Pipeline step that takes the Evidence Graph and runs all Validation Rules
    to generate a ValidationReport.
    """
    
    def __init__(self):
        self.engine = ValidationEngine()
        
    def execute(self, context: dict) -> dict:
        """
        Executes the Validation step on the provided pipeline context.
        """
        engine_context = EngineContext(
            claim_id=context.get("claim_id", "00000000-0000-0000-0000-000000000000"),
            input_data={
                "evidence_graph_result": context.get("evidence_graph_result"),
                "extraction_result": context.get("extraction_result")
            }
        )
        
        result = self.engine.process(engine_context)
        
        if result.status == EngineStatus.SUCCESS:
            context["validation_report"] = result.output_data.get("validation_report")
        else:
            context["validation_report"] = None
            context["validation_errors"] = result.errors
            
        return context
