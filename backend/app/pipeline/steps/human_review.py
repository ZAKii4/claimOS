"""
Step 16: Human Review (Routing).

Suspends pipeline if HITL is required, flagging the document for operator review.
"""

from app.pipeline.core import DocumentContext, PipelineStep


class HumanReviewStep(PipelineStep):
    
    @property
    def name(self) -> str:
        return "human_review"

    def execute(self, context: DocumentContext) -> DocumentContext:
        if context.validation_decision == "HITL_REVIEW":
            # Stub: Create ValidationFieldFlag records for specific fields
            # that lowered the confidence score, routing them to human operators.
            # In a synchronous pipeline, this simply means saving state to DB.
            pass
            
        return context
