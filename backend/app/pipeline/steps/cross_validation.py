"""
Step 14: Cross-Validation.

Compares newly extracted data against existing claim data to detect
contradictions (ClaimDiscrepancy).
"""

from app.pipeline.core import DocumentContext, PipelineStep


class CrossValidationStep(PipelineStep):
    
    @property
    def name(self) -> str:
        return "cross_validation"

    def execute(self, context: DocumentContext) -> DocumentContext:
        # Stub: Load existing claim data using context.claim_id.
        # Run business rules (e.g., Police Report date of loss == Claim date of loss).
        # If mismatch, create a ClaimDiscrepancy record.
        
        return context
