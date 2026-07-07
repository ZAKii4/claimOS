"""
Pipeline Orchestrator.

Manages the execution flow of the pipeline, error handling,
observability logging, and triggering compensation logic (Saga pattern)
if a step fails fatally.
"""

import logging
from typing import Any

from app.pipeline.core import DocumentContext, ErrorSeverity, PipelineError, PipelineStep

logger = logging.getLogger("claimOS.pipeline")


class PipelineOrchestrator:
    """
    Executes a sequence of PipelineSteps on a DocumentContext.
    """

    def __init__(self, steps: list[PipelineStep]) -> None:
        self.steps = steps

    def execute(self, context: DocumentContext) -> DocumentContext:
        """
        Run the pipeline sequentially.
        
        If a FATAL error occurs, halts execution, triggers compensate() on
        all completed steps in reverse order, and raises the error.
        If a DEGRADED error occurs, logs it and continues.
        """
        logger.info("Starting pipeline with %d steps for file: %s", len(self.steps), context.filename)
        
        completed_steps: list[PipelineStep] = []

        for step in self.steps:
            logger.info("Executing step: %s", step.name)
            try:
                # Execute the step
                context = step.execute(context)
                
                # Record success
                context.completed_steps.append(step.name)
                completed_steps.append(step)
                
            except PipelineError as e:
                self._handle_error(e, context, completed_steps)
            except Exception as e:
                # Wrap unexpected exceptions as FATAL PipelineErrors
                wrapped_error = PipelineError(
                    message=f"Unexpected exception: {str(e)}",
                    step_name=step.name,
                    severity=ErrorSeverity.FATAL,
                )
                self._handle_error(wrapped_error, context, completed_steps)

        logger.info("Pipeline completed successfully for file: %s", context.filename)
        return context

    def _handle_error(
        self, 
        error: PipelineError, 
        context: DocumentContext, 
        completed_steps: list[PipelineStep]
    ) -> None:
        """Handle errors based on severity."""
        
        # Log the error in context
        error_record = {
            "step": error.step_name,
            "severity": error.severity,
            "message": error.message,
            "details": error.details,
        }
        context.errors.append(error_record)
        
        if error.severity == ErrorSeverity.FATAL:
            logger.error("FATAL error in %s: %s. Aborting pipeline.", error.step_name, error.message)
            self._compensate(context, completed_steps)
            raise error
            
        elif error.severity == ErrorSeverity.DEGRADED:
            logger.warning("DEGRADED error in %s: %s. Continuing pipeline.", error.step_name, error.message)
            
        elif error.severity == ErrorSeverity.RETRYABLE:
            logger.warning("RETRYABLE error in %s: %s. (Retry logic not yet implemented, aborting).", error.step_name, error.message)
            # In a Celery environment, this would raise a Retry exception.
            # For synchronous MVP, we treat it as FATAL.
            self._compensate(context, completed_steps)
            raise error

    def _compensate(self, context: DocumentContext, completed_steps: list[PipelineStep]) -> None:
        """Trigger compensation logic in reverse order of execution."""
        if not completed_steps:
            return
            
        logger.info("Triggering compensation for %d steps...", len(completed_steps))
        
        for step in reversed(completed_steps):
            try:
                step.compensate(context)
                logger.debug("Successfully compensated step: %s", step.name)
            except Exception as e:
                # We log but do not raise, to ensure all compensate blocks run
                logger.error("Failed to compensate step %s: %s", step.name, str(e), exc_info=True)
