"""
Step 15: Decision Engine.

Calculates the final composite confidence score and routing decision
(ValidationDecision) based on all previous steps and discrepancies.
"""

from app.pipeline.core import DocumentContext, PipelineStep


class DecisionEngineStep(PipelineStep):
    
    @property
    def name(self) -> str:
        return "decision_engine"

    def execute(self, context: DocumentContext) -> DocumentContext:
        # Stub: Aggregate confidences from OCR, Layout, Classification, Extraction.
        # If composite_confidence > 0.95 and no critical discrepancies -> STP_APPROVED.
        # Else -> HITL_REVIEW.
        
        context.validation_decision = "HITL_REVIEW" # Default pessimistic
        
        return context
