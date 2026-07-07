"""
Step 01: Upload & Initialization.

Validates the incoming payload size and MIME type.
"""

from app.pipeline.core import DocumentContext, ErrorSeverity, PipelineError, PipelineStep


class UploadStep(PipelineStep):
    
    @property
    def name(self) -> str:
        return "upload_and_init"
        
    def __init__(self, max_size_bytes: int = 50 * 1024 * 1024) -> None:
        self.max_size_bytes = max_size_bytes
        self.allowed_mime_types = ["application/pdf", "image/jpeg", "image/png"]

    def execute(self, context: DocumentContext) -> DocumentContext:
        if not context.payload:
            raise PipelineError("Empty payload provided", self.name, ErrorSeverity.FATAL)
            
        payload_size = len(context.payload)
        if payload_size > self.max_size_bytes:
            raise PipelineError(
                f"File too large: {payload_size} bytes (max {self.max_size_bytes})", 
                self.name, 
                ErrorSeverity.FATAL
            )
            
        if context.content_type not in self.allowed_mime_types:
            raise PipelineError(
                f"Unsupported media type: {context.content_type}", 
                self.name, 
                ErrorSeverity.FATAL
            )
            
        # In a real system, we might also use python-magic here to verify the true MIME type
        
        return context
