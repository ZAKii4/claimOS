"""
Base engine contract for all AI engines.

Every engine in ``app/engines/`` must implement this abstract base class.
Engines are **totally independent modules** — they receive an
``EngineContext``, perform processing, and return an ``EngineResult``.
They never interact with repositories or services directly.

This design ensures each engine can be extracted into a standalone
microservice in the future without modifying business logic.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID


class EngineStatus(StrEnum):
    """Outcome status of an engine execution."""

    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILURE = "FAILURE"


@dataclass
class EngineContext:
    """
    Input context passed to an engine for processing.

    This is the **only** data an engine receives. It must contain
    everything the engine needs to perform its task.
    """

    claim_id: UUID
    document_id: UUID | None = None
    page_ids: list[UUID] = field(default_factory=list)
    input_data: dict[str, Any] = field(default_factory=dict)
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class EngineResult:
    """
    Output returned by an engine after processing.

    The service layer reads the result and decides what to persist
    and how to update the claim's state.
    """

    engine_name: str
    engine_version: str
    status: EngineStatus
    output_data: dict[str, Any] = field(default_factory=dict)
    confidence: float | None = None
    errors: list[str] = field(default_factory=list)
    processing_time_ms: int = 0
    processed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class BaseEngine(ABC):
    """
    Abstract base class that every AI engine must implement.

    Contract:
    - ``name`` — unique identifier for the engine (e.g. ``"ocr"``, ``"classification"``).
    - ``version`` — semantic version string.
    - ``process(context)`` — execute the engine's logic.
    - ``health_check()`` — verify the engine is operational.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique engine identifier."""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """Semantic version of the engine."""
        ...

    @abstractmethod
    def process(self, context: EngineContext) -> EngineResult:
        """
        Execute the engine's processing logic.

        Args:
            context: All input data needed for processing.

        Returns:
            An ``EngineResult`` describing the outcome.
        """
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Return ``True`` if the engine is ready to process requests."""
        ...
