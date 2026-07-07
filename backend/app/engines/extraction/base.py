from abc import ABC, abstractmethod
from typing import Any

from app.engines.extraction.models import ExtractedEntity
from app.engines.classification.models import DocumentClassificationResult
from app.engines.layout.models import LayoutAnalysisResult
from app.engines.ocr.models import OCRResult


class BaseExtractor(ABC):
    """
    Contract for every domain-specific extractor (e.g. LicensePlateExtractor, NameExtractor).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        ...
        
    @property
    @abstractmethod
    def priority(self) -> int:
        """Higher priority runs first and may win conflicts."""
        return 50

    @property
    @abstractmethod
    def supported_document_families(self) -> list[str]:
        """List of DocumentClass families this extractor applies to, or ['*'] for all."""
        ...

    def initialize(self) -> None:
        """Setup heavy resources like ML models (spaCy) or compile regexes."""
        pass

    def health_check(self) -> bool:
        return True

    @abstractmethod
    def extract(
        self, 
        ocr_result: OCRResult, 
        layout_result: LayoutAnalysisResult, 
        classification: DocumentClassificationResult
    ) -> list[ExtractedEntity]:
        """
        Main method to find entities in the document.
        Must return entities with populated Provenance.
        """
        ...

    def validate(self, entity: ExtractedEntity) -> bool:
        """Returns True if the entity meets business rules, False otherwise."""
        return True

    def normalize(self, raw_value: str) -> Any:
        """Converts raw string to standard format. Default implementation returns raw_value."""
        return raw_value
