"""
Step 17: Archiving & Audit.

Finalizes the pipeline run, marks the document as processed,
and writes an immutable ClaimEvent audit log.
"""

from app.pipeline.core import DocumentContext, PipelineStep


class ArchivingStep(PipelineStep):
    
    @property
    def name(self) -> str:
        return "archiving"

    def execute(self, context: DocumentContext) -> DocumentContext:
        # Stub: 
        # 1. Update DocumentStatus in DB to PROCESSED or REVIEW_REQUIRED.
        # 2. Write ClaimEvent (actor_type="SYSTEM") recording the pipeline completion.
        # 3. Move the physical file to cold storage (e.g. S3 standard-IA) if needed.
        
        return context
