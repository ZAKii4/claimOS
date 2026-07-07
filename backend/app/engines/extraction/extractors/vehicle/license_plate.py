import re

from app.engines.classification.models import DocumentClassificationResult
from app.engines.extraction.base import BaseExtractor
from app.engines.extraction.confidence import ConfidenceAdjuster
from app.engines.extraction.models import ExtractedEntity, Provenance
from app.engines.extraction.normalization import Normalizer
from app.engines.extraction.validation import Validator
from app.engines.layout.models import LayoutAnalysisResult
from app.engines.ocr.models import OCRResult


class LicensePlateExtractor(BaseExtractor):
    """
    Extracts vehicle license plates using Regex over OCR blocks.
    """

    @property
    def name(self) -> str:
        return "vehicle.license_plate_extractor"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def priority(self) -> int:
        return 100

    @property
    def supported_document_families(self) -> list[str]:
        # Usually found in Constat Amiable, Police Report, Repair Estimate
        return ["Police Report", "Repair Estimate", "Vehicle Registration", "*"]

    def extract(
        self, 
        ocr_result: OCRResult, 
        layout_result: LayoutAnalysisResult, 
        classification: DocumentClassificationResult
    ) -> list[ExtractedEntity]:
        
        entities = []
        # Pattern for SIV (AB-123-CD) or FNI (1234 AB 56) with flexible spacing/hyphens
        pattern = re.compile(r"\b([A-Z]{2}[\s\-]?[0-9]{3}[\s\-]?[A-Z]{2}|[0-9]{1,4}[\s\-]?[A-Z]{2,3}[\s\-]?[0-9]{2,4})\b", re.IGNORECASE)

        # Naive approach: Scan all text lines in OCR
        page_index = 0
        if ocr_result.page:
            for block in ocr_result.page.blocks:
                for line in block.lines:
                    text = " ".join(w.text for w in line.words)
                    matches = pattern.finditer(text)
                    for match in matches:
                        raw_val = match.group(0)
                        
                        # Use BoundingBox of the line as an approximation
                        bbox = None
                        if line.bbox:
                            bbox = line.bbox.model_dump()
                            
                        # OCRWord in this project does not have UUIDs, so we skip word_ids
                        word_ids = []

                        provenance = Provenance(
                            page_index=page_index,
                            bounding_box=bbox,
                            ocr_word_ids=word_ids,
                            extractor_name=self.name,
                            extraction_method="regex"
                        )
                        
                        normalized = self.normalize(raw_val)
                        is_valid = self.validate(ExtractedEntity(
                            field_name="vehicle_plate",
                            raw_value=raw_val,
                            normalized_value=normalized,
                            entity_type="vehicle",
                            confidence=0.8,
                            provenance=provenance
                        ))
                        
                        entity = ExtractedEntity(
                            field_name="vehicle_plate",
                            raw_value=raw_val,
                            normalized_value=normalized,
                            entity_type="vehicle",
                            confidence=0.8,
                            provenance=provenance
                        )
                        
                        entity.confidence = ConfidenceAdjuster.adjust(entity, is_valid)
                        
                        if entity.confidence > 0.4:
                            entities.append(entity)
                            
        return entities

    def validate(self, entity: ExtractedEntity) -> bool:
        return Validator.is_valid_license_plate(entity.normalized_value)

    def normalize(self, raw_value: str) -> str:
        return Normalizer.normalize_license_plate(raw_value)
