from typing import Type

from app.engines.classification.models import DocumentClassificationResult
from app.engines.extraction.base import BaseExtractor


class ExtractorRegistry:
    """
    Dynamic registry holding all available domain extractors.
    """
    
    def __init__(self):
        self._extractors: list[Type[BaseExtractor]] = []

    def register(self, extractor_class: Type[BaseExtractor]) -> None:
        if extractor_class not in self._extractors:
            self._extractors.append(extractor_class)

    def get_extractors_for_document(self, classification: DocumentClassificationResult) -> list[BaseExtractor]:
        """
        Returns instantiated extractors applicable to the given document classification,
        sorted by priority descending.
        """
        applicable = []
        if not classification.documents:
            return applicable
            
        # We use the primary document's family for routing
        primary_family = classification.documents[0].classification.document_class.family
        
        for cls in self._extractors:
            instance = cls()
            supported = instance.supported_document_families
            if "*" in supported or primary_family in supported:
                applicable.append(instance)
                
        # Sort by priority
        applicable.sort(key=lambda ext: ext.priority, reverse=True)
        return applicable
