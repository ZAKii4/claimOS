"""
FastAPI dependencies for the v1 API.

Centralises dependency injection for database sessions, services,
and pagination parameters.
"""

from collections.abc import Generator

from fastapi import Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.core.database import get_db
from app.models.operator import Operator
from app.security.jwt_manager import jwt_manager
from app.services.auth_service import AuthService
from app.services.claim_service import ClaimService
from app.services.document_service import DocumentService
from app.services.metrics_service import MetricsService
from app.services.validation_service import ValidationService
from app.utils.pagination import PaginationParams

_bearer_scheme = HTTPBearer(auto_error=False)


def get_claim_service(db: Session = Depends(get_db)) -> ClaimService:
    """Provide a ``ClaimService`` instance with a database session."""
    return ClaimService(db)


def get_document_service(db: Session = Depends(get_db)) -> DocumentService:
    """Provide a ``DocumentService`` instance with a database session."""
    return DocumentService(db)


def get_validation_service(db: Session = Depends(get_db)) -> ValidationService:
    """Provide a ``ValidationService`` instance with a database session."""
    return ValidationService(db)


def get_metrics_service(db: Session = Depends(get_db)) -> MetricsService:
    """Provide a ``MetricsService`` instance with a database session."""
    return MetricsService(db)


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Provide an ``AuthService`` instance with a database session."""
    return AuthService(db)


def get_current_operator(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> Operator:
    """
    Resolves the real, active Operator behind a request's Bearer token.

    Raises 401 for a missing token, an invalid/expired token, or a token
    whose subject no longer maps to an active operator — a JWT was
    previously issued at login but never actually checked by any endpoint.
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    payload = jwt_manager.decode_token(credentials.credentials)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    operator = auth_service.get_operator_by_id(payload["sub"])
    if not operator or not operator.is_active:
        raise HTTPException(status_code=401, detail="Operator not found or inactive")

    return operator


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
