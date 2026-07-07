from app.engines.base import EngineContext, EngineStatus
from app.engines.layout.manager import LayoutEngine


class LayoutAnalysisStep:
    """
    Pipeline step that takes OCR results and the original image,
    runs the Layout Analysis Engine, and updates the PageContext/DocumentContext.
    """
    
    def __init__(self):
        self.engine = LayoutEngine()
        
    def execute(self, context: dict) -> dict:
        """
        Executes the Layout Analysis step on the provided pipeline context.
        
        Args:
            context (dict): The global pipeline context. Must contain:
                            - "image_path": Path to the image.
                            - "ocr_result": The OCRResult dictionary.
                            - "claim_id": The UUID of the claim.
                            
        Returns:
            dict: The updated pipeline context with "layout_result".
        """
        # Build EngineContext from pipeline context
        engine_context = EngineContext(
            claim_id=context.get("claim_id", "00000000-0000-0000-0000-000000000000"),
            input_data={
                "image_path": context.get("image_path"),
                "ocr_result": context.get("ocr_result")
            }
        )
        
        result = self.engine.process(engine_context)
        
        if result.status == EngineStatus.SUCCESS:
            context["layout_result"] = result.output_data.get("layout_analysis_result")
            context["layout_confidence"] = result.confidence
        else:
            context["layout_result"] = None
            context["layout_errors"] = result.errors
            
        return context
