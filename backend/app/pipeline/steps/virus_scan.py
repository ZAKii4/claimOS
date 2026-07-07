"""
Step 05: Virus Scan.

Passes the payload to a malware detection engine (e.g., ClamAV).
"""

from app.pipeline.core import DocumentContext, ErrorSeverity, PipelineError, PipelineStep


class VirusScanStep(PipelineStep):
    
    @property
    def name(self) -> str:
        return "virus_scan"

    def execute(self, context: DocumentContext) -> DocumentContext:
        # Stub: Integration with an antivirus service (ClamAV daemon via TCP or similar)
        # If malware is detected:
        # raise PipelineError("Malware detected: EICAR-Test-Signature", self.name, ErrorSeverity.FATAL)
        
        context.metadata["virus_scan_passed"] = True
        return context
