from app.engines.base import EngineContext, EngineStatus
from app.engines.classification.manager import ClassificationEngine


class ClassificationStep:
    """
    Pipeline step that takes OCR and Layout results,
    runs the Intelligent Document Classification Engine, 
    and updates the DocumentContext with the document classes.
    """
    
    def __init__(self):
        self.engine = ClassificationEngine()
        
    def execute(self, context: dict) -> dict:
        """
        Executes the Classification step on the provided pipeline context.
        """
        engine_context = EngineContext(
            claim_id=context.get("claim_id", "00000000-0000-0000-0000-000000000000"),
            input_data={
                "ocr_result": context.get("ocr_result"),
                "layout_result": context.get("layout_result")
            }
        )
        
        result = self.engine.process(engine_context)
        
        if result.status == EngineStatus.SUCCESS:
            context["classification_result"] = result.output_data.get("classification_result")
        else:
            context["classification_result"] = None
            context["classification_errors"] = result.errors
            
        return context
