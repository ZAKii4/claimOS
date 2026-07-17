"""
Document-related Pydantic schemas (DTOs).
"""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.engines.form_mapping.manager import DocumentRole


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
    document_role: DocumentRole | None = None


class DocumentIngestRead(BaseModel):
    """Result of ingesting one document through the real processing pipeline."""

    id: UUID
    claim_id: UUID
    document_type: str
    document_role: DocumentRole | None = None
    classification_confidence: Decimal | None = None
    page_range_start: int
    page_range_end: int
    storage_uri: str
    created_at: datetime
    pipeline_warnings: list[str] = []


class FieldCorrectionRequest(BaseModel):
    """Manual correction of one ClaimOpeningForm field."""

    field_path: str = Field(
        description="Dotted path into ClaimOpeningForm, e.g. 'numero_police' or "
        "'conducteur.nom'. Must resolve to a MappedField — list items "
        "(victimes[i].*) are not yet correctable this way."
    )
    value: Any = Field(description="The corrected value. Use null to clear a field.")


class ManualOpeningFormRequest(BaseModel):
    """
    Bulk manual entry of a claim's opening form — the "no document" path for
    registering a sinistre, as an alternative to uploading documents through
    ``POST /claims/{claim_id}/documents``.

    ``fields`` uses the same dotted-path convention as ``FieldCorrectionRequest``
    (e.g. {"numero_police": "AXA123", "conducteur.nom": "Dupont"}), applied in
    one transaction. Can also be used later to fill in fields an upload didn't
    cover — the two paths are not mutually exclusive.
    """

    fields: dict[str, Any] = Field(
        description="Dotted ClaimOpeningForm path -> value, e.g. "
        "{'numero_police': 'AXA123', 'lieu_survenance': 'Casablanca'}."
    )
