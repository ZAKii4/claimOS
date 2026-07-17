"""
Unit tests for the Document Processing Pipeline orchestrator.
"""

import pytest

from app.pipeline import get_document_pipeline
from app.pipeline.core import DocumentContext, ErrorSeverity, PipelineError, PipelineStep
from app.pipeline.orchestrator import PipelineOrchestrator


class MockSuccessStep(PipelineStep):
    @property
    def name(self) -> str:
        return "mock_success"

    def execute(self, context: DocumentContext) -> DocumentContext:
        context.metadata["mock_success_ran"] = True
        return context

    def compensate(self, context: DocumentContext) -> None:
        context.metadata["mock_success_compensated"] = True


class MockFatalErrorStep(PipelineStep):
    @property
    def name(self) -> str:
        return "mock_fatal"

    def execute(self, context: DocumentContext) -> DocumentContext:
        raise PipelineError("Fatal test error", self.name, ErrorSeverity.FATAL)


class MockDegradedErrorStep(PipelineStep):
    @property
    def name(self) -> str:
        return "mock_degraded"

    def execute(self, context: DocumentContext) -> DocumentContext:
        raise PipelineError("Degraded test error", self.name, ErrorSeverity.DEGRADED)


def test_pipeline_success():
    """Test a successful pipeline run."""
    steps = [MockSuccessStep(), MockSuccessStep()]
    orchestrator = PipelineOrchestrator(steps)
    
    context = DocumentContext(payload=b"test")
    result = orchestrator.execute(context)
    
    assert result.metadata["mock_success_ran"] is True
    assert len(result.completed_steps) == 2
    assert len(result.errors) == 0


def test_pipeline_saga_compensation():
    """Test that a FATAL error triggers compensation on completed steps."""
    steps = [MockSuccessStep(), MockFatalErrorStep()]
    orchestrator = PipelineOrchestrator(steps)
    
    context = DocumentContext(payload=b"test")
    
    with pytest.raises(PipelineError) as exc_info:
        orchestrator.execute(context)
        
    assert exc_info.value.severity == ErrorSeverity.FATAL
    assert exc_info.value.step_name == "mock_fatal"
    
    # Check that the first step ran successfully
    assert "mock_success" in context.completed_steps
    # Check that the first step's compensate() was called
    assert context.metadata.get("mock_success_compensated") is True
    # Ensure errors are logged in context
    assert len(context.errors) == 1
    assert context.errors[0]["step"] == "mock_fatal"


def test_pipeline_degraded_continuation():
    """Test that a DEGRADED error logs but allows pipeline to continue."""
    steps = [MockDegradedErrorStep(), MockSuccessStep()]
    orchestrator = PipelineOrchestrator(steps)
    
    context = DocumentContext(payload=b"test")
    
    # Should not raise exception
    result = orchestrator.execute(context)
    
    # Second step should still run
    assert "mock_success" in result.completed_steps
    assert result.metadata.get("mock_success_ran") is True
    
    # Degraded error should be in context.errors
    assert len(result.errors) == 1
    assert result.errors[0]["severity"] == ErrorSeverity.DEGRADED
    assert result.errors[0]["step"] == "mock_degraded"


def _build_minimal_pdf_bytes() -> bytes:
    """Build a real, valid single-page PDF (not a stub/mock payload)."""
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), "POLICY NO: TEST-000000")
    page.insert_text((50, 120), "PLATE: AA-000-AA")
    return doc.tobytes()


def test_real_document_pipeline_runs_end_to_end_without_crashing():
    """
    Regression test for the wired factory pipeline (`get_document_pipeline()`).

    Every step must implement the `PipelineStep` interface (a `.name` property
    and `execute(DocumentContext) -> DocumentContext`). A prior interface
    mismatch (some steps written against a plain-dict context instead of
    `DocumentContext`) caused this exact call to crash with an
    `AttributeError` on the second step — never caught because no test
    exercised the real factory, only hand-written mock steps.

    Uses a real, valid PDF (rendered via PyMuPDF in page_extraction) rather
    than a placeholder payload, since page extraction now genuinely rasterizes
    the document instead of hardcoding a page count.
    """
    pipeline = get_document_pipeline()
    context = DocumentContext(
        payload=_build_minimal_pdf_bytes(),
        filename="test.pdf",
        content_type="application/pdf",
    )

    result = pipeline.execute(context)

    expected_steps = [
        "upload_and_init", "fingerprint", "metadata_extraction", "virus_scan",
        "storage", "page_extraction", "iqa_assessment", "preprocessing", "ocr",
        "layout_analysis", "classification", "business_extraction",
        "evidence_graph", "cross_validation", "decision_engine",
        "human_review", "archiving",
    ]
    assert result.completed_steps == expected_steps
    assert result.errors == []
    assert len(result.pages) == 1
    assert result.validation_decision is not None
