import uuid
from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.engines.classification.models import DocumentClass


class Provenance(BaseModel):
    """Total traceability of extracted data to its source in the document."""
    page_index: int
    bounding_box: Optional[dict[str, float]] = Field(default=None, description="Coordinates in the image")
    ocr_word_ids: list[str] = Field(default_factory=list, description="Linked OCR word UUIDs if applicable")
    layout_region_id: Optional[str] = Field(default=None, description="Linked Layout Region UUID if applicable")
    extractor_name: str
    extraction_method: str = Field(default="regex", description="regex, spacy, layout_key_value, etc.")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0"


class ExtractedEntity(BaseModel):
    """A single piece of information extracted from a document."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    field_name: str = Field(description="Internal standardized name (e.g., 'vehicle_plate', 'policy_number')")
    raw_value: str = Field(description="The exact text found in the document")
    normalized_value: Any = Field(description="The parsed/casted value (e.g. standard Date, float, or formatted string)")
    entity_type: str = Field(description="e.g. 'person', 'vehicle', 'date', 'amount'")
    confidence: float = Field(ge=0.0, le=1.0)
    provenance: Provenance
    
    def __hash__(self):
        return hash((self.field_name, self.normalized_value))

    def __eq__(self, other):
        if not isinstance(other, ExtractedEntity):
            return False
        return self.field_name == other.field_name and self.normalized_value == other.normalized_value


class EntityEdge(BaseModel):
    """Represents a relationship between two entities."""
    source_id: str
    target_id: str
    relation_type: str = Field(description="e.g. 'OWNS', 'DRIVES', 'INVOLVED_IN'")


class EntityGroup(BaseModel):
    """A logical grouping of related entities, forming a flat graph."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    group_type: str = Field(description="e.g., 'Vehicle A', 'Victim', 'Insurance Context'")
    entities: list[ExtractedEntity] = Field(default_factory=list)


class ExtractionResult(BaseModel):
    """The final output of the Extraction Engine."""
    document_class: DocumentClass
    groups: list[EntityGroup] = Field(default_factory=list)
    loose_entities: list[ExtractedEntity] = Field(default_factory=list, description="Entities not bound to a group")
    edges: list[EntityEdge] = Field(default_factory=list, description="Relationships between entities/groups")
    global_confidence: float
    execution_time_ms: int
    extractors_used: list[str] = Field(default_factory=list)
