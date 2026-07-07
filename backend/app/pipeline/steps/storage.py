"""
Step 06: Storage.

Saves the physical payload to an object storage (S3 or local filesystem),
updates the context with the URI, and clears the payload from RAM.
"""

import os
import uuid

from app.config.settings import get_settings
from app.pipeline.core import DocumentContext, ErrorSeverity, PipelineError, PipelineStep


class StorageStep(PipelineStep):
    
    @property
    def name(self) -> str:
        return "storage"
        
    def __init__(self) -> None:
        self.settings = get_settings()
        os.makedirs(self.settings.UPLOAD_DIR, exist_ok=True)

    def execute(self, context: DocumentContext) -> DocumentContext:
        if not context.payload:
            raise PipelineError("No payload to store", self.name, ErrorSeverity.FATAL)
            
        # Generate a unique filename using SHA256 and UUID
        ext = context.filename.split('.')[-1] if '.' in context.filename else "bin"
        unique_name = f"{context.fingerprint_sha256 or uuid.uuid4().hex}.{ext}"
        file_path = os.path.join(self.settings.UPLOAD_DIR, unique_name)
        
        try:
            with open(file_path, "wb") as f:
                f.write(context.payload)
        except Exception as e:
            raise PipelineError(f"Failed to write to storage: {e}", self.name, ErrorSeverity.FATAL)
            
        context.storage_uri = f"local://{file_path}"
        
        # CRITICAL: Free RAM. We no longer need the raw payload in memory.
        context.payload = None
        
        return context

    def compensate(self, context: DocumentContext) -> None:
        """Rollback: Delete the stored file if a subsequent step fails."""
        if context.storage_uri and context.storage_uri.startswith("local://"):
            file_path = context.storage_uri.replace("local://", "")
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
