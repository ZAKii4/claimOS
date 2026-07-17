import re

from app.engines.classification.models import DocumentClassificationResult
from app.engines.extraction.base import BaseExtractor
from app.engines.extraction.confidence import ConfidenceAdjuster
from app.engines.extraction.models import ExtractedEntity, Provenance
from app.engines.extraction.normalization import Normalizer
from app.engines.layout.models import LayoutAnalysisResult
from app.engines.ocr.models import OCRResult

BRAND_LABEL = re.compile(r"marque\s*[:\-]\s*(.+)", re.IGNORECASE)


class VehicleBrandExtractor(BaseExtractor):
    """Extracts the vehicle brand ("Marque") from key/value style document text."""

    @property
    def name(self) -> str:
        return "vehicle.brand_extractor"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def priority(self) -> int:
        return 70

    @property
    def supported_document_families(self) -> list[str]:
        return ["Vehicle Registration", "Insurance Attestation", "*"]

    def extract(
        self,
        ocr_result: OCRResult,
        layout_result: LayoutAnalysisResult,
        classification: DocumentClassificationResult,
    ) -> list[ExtractedEntity]:
        entities: list[ExtractedEntity] = []
        if not ocr_result.page:
            return entities

        page_index = 0
        for block in ocr_result.page.blocks:
            for line in block.lines:
                text = " ".join(w.text for w in line.words)
                match = BRAND_LABEL.match(text.strip())
                if not match:
                    continue

                raw_val = match.group(1).strip()
                if not raw_val or not self.validate_format(raw_val):
                    continue

                normalized = self.normalize(raw_val)
                bbox = line.bbox.model_dump() if line.bbox else None

                provenance = Provenance(
                    page_index=page_index,
                    bounding_box=bbox,
                    extractor_name=self.name,
                    extraction_method="regex",
                )

                entity = ExtractedEntity(
                    field_name="vehicle_brand",
                    raw_value=raw_val,
                    normalized_value=normalized,
                    entity_type="vehicle",
                    confidence=0.7,
                    provenance=provenance,
                )
                entity.confidence = ConfidenceAdjuster.adjust(entity, True)

                if entity.confidence > 0.4:
                    entities.append(entity)

        return entities

    def validate_format(self, value: str) -> bool:
        return bool(re.fullmatch(r"[A-Za-zÀ-ÿ0-9' \-]{2,40}", value))

    def normalize(self, raw_value: str) -> str:
        return Normalizer.normalize_text(raw_value).upper()
