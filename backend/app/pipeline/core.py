"""
Core contracts for the Document Processing Pipeline.

Provides the State Machine context (`DocumentContext`), the step interface
(`PipelineStep`), and structured exception handling (`PipelineError`).
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from app.engines.base import EngineResult


class ErrorSeverity(StrEnum):
    """
    Severity levels for pipeline errors.
    
    - FATAL: Cannot continue, abort pipeline.
    - RETRYABLE: Temporary failure, can be retried later.
    - DEGRADED: Continue, but flag for human review.
    """
    FATAL = "FATAL"
    RETRYABLE = "RETRYABLE"
    DEGRADED = "DEGRADED"


class PipelineError(Exception):
    """Exception raised by a PipelineStep upon failure."""
    
    def __init__(
        self, 
        message: str, 
        step_name: str, 
        severity: ErrorSeverity = ErrorSeverity.FATAL,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.step_name = step_name
        self.severity = severity
        self.details = details or {}
        super().__init__(f"[{severity}] {step_name}: {message}")


@dataclass
class PageContext:
    """State for a single extracted page of the document."""
    
    page_number: int
    original_page_number: int
    image_uri: str | None = None
    ocr_hocr_uri: str | None = None
    resolution_dpi: int = 300
    orientation_corrected_deg: int = 0
    extracted_text: str | None = None
    engine_results: dict[str, EngineResult] = field(default_factory=dict)


@dataclass
class DocumentContext:
    """
    The shared state object traversing the pipeline.
    
    It accumulates data as it passes through each PipelineStep.
    Designed to be robust and observable.
    """
    
    # 1. Input Payload (Cleared after Storage step to save RAM)
    payload: bytes | None = None
    filename: str = "unknown"
    content_type: str = "application/octet-stream"
    
    # 2. Database Identities (Populated as entities are created)
    claim_id: uuid.UUID | None = None
    document_id: uuid.UUID | None = None
    
    # 3. Document Physical Properties
    storage_uri: str | None = None
    fingerprint_sha256: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # 4. Processing State
    pages: list[PageContext] = field(default_factory=list)
    engine_results: dict[str, EngineResult] = field(default_factory=dict)
    extracted_data: dict[str, Any] = field(default_factory=dict)
    
    # 5. Routing & Decisions
    document_type_code: str | None = None
    is_duplicate: bool = False
    validation_decision: str | None = None
    
    # 6. Observability & Audit
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_steps: list[str] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)


class PipelineStep(ABC):
    """
    Contract for every isolated step in the document lifecycle.
    
    Each step must implement `execute()` to perform its logic.
    Optionally, it can implement `compensate()` to rollback side effects
    if a subsequent step fails (Saga pattern).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for the step (e.g., 'virus_scan', 'ocr')."""
        pass

    @abstractmethod
    def execute(self, context: DocumentContext) -> DocumentContext:
        """
        Execute the step's logic and return the enriched context.
        
        Raises:
            PipelineError: If the step fails.
        """
        pass

    def compensate(self, context: DocumentContext) -> None:
        """
        Rollback side effects if the pipeline aborts later.
        
        Examples: Delete files from S3, soft-delete DB records.
        """
        pass
