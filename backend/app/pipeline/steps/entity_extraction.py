from app.engines.base import EngineContext, EngineStatus
from app.engines.extraction.manager import ExtractionEngine
from app.engines.extraction.registry import ExtractorRegistry
from app.engines.extraction.extractors.vehicle.license_plate import LicensePlateExtractor
from app.engines.extraction.extractors.insurance.policy_number import PolicyNumberExtractor


class EntityExtractionStep:
    """
    Pipeline step that takes OCR, Layout, and Classification results,
    runs the Intelligent Entity Extraction Engine, 
    and updates the DocumentContext with the extracted business data.
    """
    
    def __init__(self):
        # Register available extractors
        registry = ExtractorRegistry()
        registry.register(LicensePlateExtractor)
        registry.register(PolicyNumberExtractor)
        
        self.engine = ExtractionEngine(registry=registry)
        
    def execute(self, context: dict) -> dict:
        """
        Executes the Extraction step on the provided pipeline context.
        """
        engine_context = EngineContext(
            claim_id=context.get("claim_id", "00000000-0000-0000-0000-000000000000"),
            input_data={
                "ocr_result": context.get("ocr_result"),
                "layout_result": context.get("layout_result"),
                "classification_result": context.get("classification_result")
            }
        )
        
        result = self.engine.process(engine_context)
        
        if result.status == EngineStatus.SUCCESS:
            context["extraction_result"] = result.output_data.get("extraction_result")
        else:
            context["extraction_result"] = None
            context["extraction_errors"] = result.errors
            
        return context
