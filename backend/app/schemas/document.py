"""
Document-related Pydantic schemas (DTOs).
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentPageRead(BaseModel):
    """Read schema for a single document page."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    page_number: int
    original_page_number: int
    image_uri: str
    ocr_hocr_uri: str
    orientation_corrected_deg: int | None = 0
    resolution_dpi: int
    quality_score: Decimal | None = None
    is_missing_detected: bool
    created_at: datetime


class DocumentRead(BaseModel):
    """Read schema for a claim document."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    claim_id: UUID
    document_type_id: UUID
    classification_confidence: Decimal | None = None
    page_range_start: int
    page_range_end: int
    language: str
    is_duplicate: bool
    duplicate_of_id: UUID | None = None
    storage_uri: str
    created_at: datetime

    # Denormalised lookup
    document_type_code: str | None = None
