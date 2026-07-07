"""
Step 03: Fingerprint (SHA256).

Calculates a cryptographic hash of the payload to detect exact duplicates.
"""

import hashlib

from app.pipeline.core import DocumentContext, PipelineStep


class FingerprintStep(PipelineStep):
    
    @property
    def name(self) -> str:
        return "fingerprint"

    def execute(self, context: DocumentContext) -> DocumentContext:
        if context.payload:
            sha256_hash = hashlib.sha256(context.payload).hexdigest()
            context.fingerprint_sha256 = sha256_hash
            
            # In a real system, we would query the DocumentRepository here
            # to check if `sha256_hash` already exists.
            # If so, we might set context.is_duplicate = True
            
        return context
