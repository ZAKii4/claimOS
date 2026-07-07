"""
Unit tests for the Document Processing Pipeline orchestrator.
"""

import pytest

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
