import time

from app.engines.base import BaseEngine, EngineContext, EngineResult, EngineStatus
from app.engines.classification.models import DocumentClassificationResult
from app.engines.extraction.models import ExtractionResult, EntityGroup
from app.engines.extraction.registry import ExtractorRegistry
from app.engines.extraction.resolver import EntityResolver
from app.engines.layout.models import LayoutAnalysisResult
from app.engines.ocr.models import OCRResult


class ExtractionEngine(BaseEngine):
    """
    Core functional engine that coordinates domain-specific extractors 
    to populate the final business data model.
    """

    def __init__(self, registry: ExtractorRegistry | None = None):
        self.registry = registry or ExtractorRegistry()
        self.resolver = EntityResolver()

    @property
    def name(self) -> str:
        return "extraction"

    @property
    def version(self) -> str:
        return "1.0.0"

    def health_check(self) -> bool:
        return True

    def process(self, context: EngineContext) -> EngineResult:
        start_time = time.time()
        
        try:
            ocr_data = context.input_data.get("ocr_result")
            layout_data = context.input_data.get("layout_result")
            classification_data = context.input_data.get("classification_result")
            
            if not ocr_data or not layout_data or not classification_data:
                return self._create_failure("Missing upstream results (ocr, layout, or classification).")

            ocr_result = OCRResult(**ocr_data) if isinstance(ocr_data, dict) else ocr_data
            layout_result = LayoutAnalysisResult(**layout_data) if isinstance(layout_data, dict) else layout_data
            classification_result = DocumentClassificationResult(**classification_data) if isinstance(classification_data, dict) else classification_data
            
            # 1. Fetch appropriate extractors via Registry
            extractors = self.registry.get_extractors_for_document(classification_result)
            
            # 2. Execute Extractors
            raw_entities = []
            extractors_used = []
            for ext in extractors:
                ext.initialize()
                entities = ext.extract(ocr_result, layout_result, classification_result)
                raw_entities.extend(entities)
                extractors_used.append(ext.name)
                
            # 3. Resolve conflicts
            resolved_entities = self.resolver.resolve(raw_entities)
            
            # 4. Grouping & Formatting (Simulated single group for MVP)
            # In a real scenario, logic would separate entities into Groups based on context (e.g. Victim vs Driver)
            global_group = EntityGroup(
                group_type="Global",
                entities=resolved_entities
            )
            
            overall_confidence = sum(e.confidence for e in resolved_entities) / len(resolved_entities) if resolved_entities else 0.0
            
            result_obj = ExtractionResult(
                document_class=classification_result.documents[0].classification.document_class,
                groups=[global_group],
                global_confidence=overall_confidence,
                execution_time_ms=int((time.time() - start_time) * 1000),
                extractors_used=extractors_used
            )
            
            return EngineResult(
                engine_name=self.name,
                engine_version=self.version,
                status=EngineStatus.SUCCESS,
                output_data={"extraction_result": result_obj.model_dump(mode='json')},
                confidence=overall_confidence,
                processing_time_ms=result_obj.execution_time_ms,
                errors=[]
            )

        except Exception as e:
            return self._create_failure(str(e))

    def _create_failure(self, error_msg: str) -> EngineResult:
        return EngineResult(
            engine_name=self.name,
            engine_version=self.version,
            status=EngineStatus.FAILURE,
            errors=[error_msg]
        )
