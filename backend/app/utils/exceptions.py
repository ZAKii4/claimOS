"""
Custom business exceptions for claimOS.

Each exception maps to a specific HTTP status code and is handled
globally by the FastAPI exception handlers in ``app/main.py``.
"""


class ClaimOSException(Exception):
    """Base exception for all claimOS business errors."""

    def __init__(self, detail: str = "An unexpected error occurred.") -> None:
        self.detail = detail
        super().__init__(self.detail)


class EntityNotFoundError(ClaimOSException):
    """Raised when a requested entity does not exist (→ HTTP 404)."""

    def __init__(self, entity: str, identifier: str) -> None:
        self.entity = entity
        self.identifier = identifier
        super().__init__(f"{entity} with identifier '{identifier}' not found.")


class DuplicateEntityError(ClaimOSException):
    """Raised when a unique constraint would be violated (→ HTTP 409)."""

    def __init__(self, entity: str, field: str, value: str) -> None:
        super().__init__(
            f"{entity} with {field}='{value}' already exists."
        )


class BusinessValidationError(ClaimOSException):
    """Raised when a business rule is violated (→ HTTP 422)."""

    def __init__(self, detail: str) -> None:
        super().__init__(detail)


class EngineProcessingError(ClaimOSException):
    """Raised when an AI engine fails to process input (→ HTTP 502)."""

    def __init__(self, engine_name: str, detail: str) -> None:
        self.engine_name = engine_name
        super().__init__(f"Engine '{engine_name}' processing failed: {detail}")
