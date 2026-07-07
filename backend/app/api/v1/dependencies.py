"""
FastAPI dependencies for the v1 API.

Centralises dependency injection for database sessions, services,
and pagination parameters.
"""

from collections.abc import Generator

from fastapi import Depends, Query
from sqlalchemy.orm import Session

from app.config.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.core.database import get_db
from app.services.claim_service import ClaimService
from app.utils.pagination import PaginationParams


def get_claim_service(db: Session = Depends(get_db)) -> ClaimService:
    """Provide a ``ClaimService`` instance with a database session."""
    return ClaimService(db)


def get_pagination(
    skip: int = Query(0, ge=0, description="Number of items to skip."),
    limit: int = Query(
        DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description="Maximum number of items to return.",
    ),
) -> PaginationParams:
    """Parse and validate pagination query parameters."""
    return PaginationParams(skip=skip, limit=limit)
