"""
Pagination utilities.

Provides a standardised ``PaginationParams`` that FastAPI endpoints
use as a dependency to parse ``skip`` / ``limit`` query parameters.
"""

from dataclasses import dataclass

from app.config.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


@dataclass(frozen=True)
class PaginationParams:
    """Validated pagination parameters."""

    skip: int = 0
    limit: int = DEFAULT_PAGE_SIZE

    def __post_init__(self) -> None:
        # Enforce bounds via object.__setattr__ because the dataclass is frozen.
        if self.skip < 0:
            object.__setattr__(self, "skip", 0)
        if self.limit < 1:
            object.__setattr__(self, "limit", 1)
        if self.limit > MAX_PAGE_SIZE:
            object.__setattr__(self, "limit", MAX_PAGE_SIZE)
