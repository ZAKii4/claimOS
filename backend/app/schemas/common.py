"""
Common Pydantic schemas used across the API.

Provides standardised response wrappers, error formats, and
generic lookup table representations.
"""

from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


# ── Pagination ───────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel, Generic[T]):
    """Standardised paginated response envelope."""

    items: list[T]
    total: int = Field(..., description="Total number of items matching the query.")
    skip: int = Field(0, description="Number of items skipped.")
    limit: int = Field(20, description="Maximum items returned per page.")


# ── Errors ───────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """Standardised error response body."""

    detail: str
    error_code: str | None = None


# ── Health ───────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    version: str
    environment: str
    database: str = "connected"


# ── Lookups ──────────────────────────────────────────────────────────────────

class LookupSchema(BaseModel):
    """Generic read schema for lookup / reference tables."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str


class LabelledLookupSchema(LookupSchema):
    """Lookup schema with bilingual labels."""

    label_fr: str
    label_ar: str


# ── Timestamps ───────────────────────────────────────────────────────────────

class TimestampSchema(BaseModel):
    """Mixin fields for timestamps."""

    model_config = ConfigDict(from_attributes=True)

    created_at: datetime
    updated_at: datetime
