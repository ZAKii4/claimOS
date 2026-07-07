from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class DocumentClass(BaseModel):
    """Represents the taxonomy of a document."""
    family: str = Field(description="Level 1 classification (e.g. Police Report, Medical Certificate)")
    subtype: Optional[str] = Field(default=None, description="Level 2 classification (e.g. PV Gendarmerie)")
    version: Optional[str] = Field(default=None, description="Level 3 classification (e.g. Modèle Assurance A)")

    model_config = ConfigDict(extra="allow")

    def __hash__(self):
        return hash((self.family, self.subtype, self.version))
        
    def __eq__(self, other):
        if not isinstance(other, DocumentClass):
            return False
        return (self.family, self.subtype, self.version) == (other.family, other.subtype, other.version)


class ClassificationPrediction(BaseModel):
    """A single prediction from a classifier or ensemble."""
    document_class: DocumentClass
    confidence: float
    explanation: Optional[str] = None
    engines_used: list[str] = Field(default_factory=list)


class SimilarityResult(BaseModel):
    """Result from the Similarity Engine."""
    document_class: DocumentClass
    distance: float
    metric: str = "cosine"
    probability: float


class PageClassification(BaseModel):
    """Classification details for a specific page."""
    page_index: int
    is_first_page: bool = False
    is_last_page: bool = False
    prediction: ClassificationPrediction


class LogicalDocument(BaseModel):
    """A logical document potentially spanning multiple pages inside a single PDF."""
    document_index: int
    page_indices: list[int]
    classification: ClassificationPrediction
    similar_documents: list[SimilarityResult] = Field(default_factory=list)


class DocumentClassificationResult(BaseModel):
    """Final output of the Classification Engine."""
    documents: list[LogicalDocument] = Field(default_factory=list)
    global_confidence: float
    execution_time_ms: int = 0
    features_extracted: dict[str, Any] = Field(default_factory=dict)
