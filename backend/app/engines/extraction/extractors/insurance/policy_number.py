from app.engines.classification.models import DocumentClassificationResult
from app.engines.extraction.base import BaseExtractor
from app.engines.extraction.confidence import ConfidenceAdjuster
from app.engines.extraction.models import ExtractedEntity, Provenance
from app.engines.extraction.normalization import Normalizer
from app.engines.extraction.validation import Validator
from app.engines.layout.models import LayoutAnalysisResult, FormFieldRegion
from app.engines.ocr.models import OCRResult


class PolicyNumberExtractor(BaseExtractor):
    """
    Extracts insurance policy numbers by looking at Layout Form Fields.
    """

    @property
    def name(self) -> str:
        return "insurance.policy_number_extractor"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def priority(self) -> int:
        return 90

    @property
    def supported_document_families(self) -> list[str]:
        return ["*"]

    def extract(
        self, 
        ocr_result: OCRResult, 
        layout_result: LayoutAnalysisResult, 
        classification: DocumentClassificationResult
    ) -> list[ExtractedEntity]:
        
        entities = []
        page_index = 0
        
        # We rely strictly on Layout Forms for this extractor
        if not layout_result.document or not layout_result.document.pages:
            return entities
            
        layout_page = layout_result.document.pages[0]
        
        for field in layout_page.form_fields:
            if not isinstance(field, FormFieldRegion):
                continue
                
            label = field.label_text.lower()
            if "police" in label or "contrat" in label:
                if field.value_text:
                    raw_val = field.value_text
                    
                    bbox = None
                    if field.bounding_box:
                        bbox = field.bounding_box.model_dump()
                        
                    provenance = Provenance(
                        page_index=page_index,
                        bounding_box=bbox,
                        layout_region_id=str(field.id),
                        extractor_name=self.name,
                        extraction_method="layout_key_value"
                    )
                    
                    normalized = self.normalize(raw_val)
                    
                    entity = ExtractedEntity(
                        field_name="policy_number",
                        raw_value=raw_val,
                        normalized_value=normalized,
                        entity_type="insurance",
                        confidence=0.9,  # High confidence because it came from a KV form
                        provenance=provenance
                    )
                    
                    is_valid = self.validate(entity)
                    entity.confidence = ConfidenceAdjuster.adjust(entity, is_valid)
                    
                    if entity.confidence > 0.4:
                        entities.append(entity)
                        
        return entities

    def validate(self, entity: ExtractedEntity) -> bool:
        return Validator.is_valid_policy_number(entity.normalized_value)

    def normalize(self, raw_value: str) -> str:
        return Normalizer.normalize_text(raw_value)
