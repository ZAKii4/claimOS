import time
from typing import Any

from app.engines.base import BaseEngine, EngineContext, EngineResult, EngineStatus
from app.engines.classification.classifier import OCRClassifier, VisualClassifier
from app.engines.classification.confidence import ConfidenceEngine
from app.engines.classification.ensemble import EnsembleClassifier
from app.engines.classification.features import FeatureExtractor
from app.engines.classification.models import DocumentClassificationResult, LogicalDocument, PageClassification
from app.engines.classification.rules import RulesClassifier
from app.engines.layout.models import LayoutAnalysisResult
from app.engines.ocr.models import OCRResult


class ClassificationEngine(BaseEngine):
    """
    Main entry point for Intelligent Document Classification.
    Coordinates feature extraction, multi-page grouping, and ensemble classification.
    """

    def __init__(self):
        self.feature_extractor = FeatureExtractor()
        
        classifiers = [
            RulesClassifier(),
            OCRClassifier(),
            VisualClassifier()
        ]
        
        self.ensemble = EnsembleClassifier(classifiers)
        self.confidence_engine = ConfidenceEngine(unknown_threshold=0.4)

    @property
    def name(self) -> str:
        return "classification"

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
            
            if not ocr_data or not layout_data:
                return self._create_failure("ocr_result and layout_result are required.")

            if isinstance(ocr_data, dict):
                ocr_result = OCRResult(**ocr_data)
            else:
                ocr_result = ocr_data
                
            if isinstance(layout_data, dict):
                layout_result = LayoutAnalysisResult(**layout_data)
            else:
                layout_result = layout_data
                
            # For simplicity, we assume 1 page = 1 logical document here,
            # but this loop can easily be extended to group pages by similarity.
            
            ocr_page = ocr_result.page
            # Assume single page layout for now as per current architecture limits
            layout_page = layout_result.document.pages[0] if layout_result.document.pages else None

            # 1. Extract Features
            features = self.feature_extractor.extract_all(ocr_page, layout_page)

            # 2. Ensemble Classification
            raw_predictions = self.ensemble.predict_ensemble(features)
            
            # 3. Confidence Evaluation
            final_predictions = self.confidence_engine.evaluate(raw_predictions)
            
            # Create Logical Document representation
            # Here we wrap the first prediction into the single logical document.
            logical_doc = LogicalDocument(
                document_index=0,
                page_indices=[0],
                classification=final_predictions[0]
            )
            
            result_obj = DocumentClassificationResult(
                documents=[logical_doc],
                global_confidence=final_predictions[0].confidence,
                execution_time_ms=int((time.time() - start_time) * 1000),
                features_extracted=features
            )
            
            return EngineResult(
                engine_name=self.name,
                engine_version=self.version,
                status=EngineStatus.SUCCESS,
                output_data={"classification_result": result_obj.model_dump(mode='json')},
                confidence=result_obj.global_confidence,
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
