"""
Step 12: Business Extraction.

Routes the document to the appropriate domain-specific Extraction BaseEngine
(e.g., PoliceReportExtractionEngine) based on the classification result.
"""

from app.pipeline.core import DocumentContext, PipelineStep


class BusinessExtractionStep(PipelineStep):
    
    @property
    def name(self) -> str:
        return "business_extraction"

    def execute(self, context: DocumentContext) -> DocumentContext:
        if not context.document_type_code:
            return context
            
        # Stub: Factory pattern to get the right engine based on type
        # engine = ExtractionEngineFactory.get_engine(context.document_type_code)
        # engine_result = engine.process(...)
        
        # We store the Key-Value Pairs in extracted_data
        context.extracted_data = {
            "stub_field": "stub_value"
        }
        
        return context
