import re

from app.engines.classification.models import DocumentClassificationResult
from app.engines.extraction.base import BaseExtractor
from app.engines.extraction.confidence import ConfidenceAdjuster
from app.engines.extraction.models import ExtractedEntity, Provenance
from app.engines.extraction.normalization import Normalizer
from app.engines.layout.models import LayoutAnalysisResult
from app.engines.ocr.models import OCRResult

# Moroccan CNIE format: 1-2 uppercase letters followed by 4-7 digits
# (e.g. BE865779, BK46962, AA111). Deliberately narrow to avoid matching
# plain license-plate-style tokens (which use fixed 3-digit blocks).
CNIE_PATTERN = re.compile(r"\b([A-Z]{1,2}\d{4,7})\b")


class NationalIdExtractor(BaseExtractor):
    """Extracts a national ID number (CNIE) from key/value style document text."""

    @property
    def name(self) -> str:
        return "insurance.national_id_extractor"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def priority(self) -> int:
        return 90

    @property
    def supported_document_families(self) -> list[str]:
        return ["Vehicle Registration", "Insurance Attestation", "Identity Card", "*"]

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
                match = CNIE_PATTERN.search(text)
                if not match:
                    continue

                raw_val = match.group(1)
                normalized = self.normalize(raw_val)
                bbox = line.bbox.model_dump() if line.bbox else None

                provenance = Provenance(
                    page_index=page_index,
                    bounding_box=bbox,
                    extractor_name=self.name,
                    extraction_method="regex",
                )

                is_valid = self.validate_format(normalized)
                entity = ExtractedEntity(
                    field_name="national_id",
                    raw_value=raw_val,
                    normalized_value=normalized,
                    entity_type="identifier",
                    confidence=0.75,
                    provenance=provenance,
                )
                entity.confidence = ConfidenceAdjuster.adjust(entity, is_valid)

                if entity.confidence > 0.4:
                    entities.append(entity)

        return entities

    def validate_format(self, value: str) -> bool:
        return bool(re.fullmatch(r"[A-Z]{1,2}\d{4,7}", value))

    def normalize(self, raw_value: str) -> str:
        return Normalizer.normalize_text(raw_value).upper().replace(" ", "")
