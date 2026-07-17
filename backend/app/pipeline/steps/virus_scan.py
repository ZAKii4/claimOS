"""
Step 05: Virus Scan.

Streams the payload to a real ClamAV daemon (INSTREAM protocol) via the
`clamd` client. A detected infection is FATAL — the pipeline must not store
or process an infected upload. An unreachable daemon DEGRADES (recorded as
a real warning, `virus_scan_passed` left `None`) rather than silently
reporting a clean scan that never happened — the previous stub always set
`virus_scan_passed = True` unconditionally, which is indistinguishable from
an infected file that was never actually checked.
"""

import io

from app.config.settings import get_settings
from app.pipeline.core import DocumentContext, ErrorSeverity, PipelineError, PipelineStep


class VirusScanStep(PipelineStep):

    @property
    def name(self) -> str:
        return "virus_scan"

    def execute(self, context: DocumentContext) -> DocumentContext:
        if not context.payload:
            return context

        import clamd

        settings = get_settings()
        try:
            client = clamd.ClamdNetworkSocket(
                host=settings.CLAMAV_HOST, port=settings.CLAMAV_PORT, timeout=15
            )
            client.ping()
            result = client.instream(io.BytesIO(context.payload))
        except PipelineError:
            raise
        except Exception as e:
            context.errors.append({
                "step": self.name,
                "severity": ErrorSeverity.DEGRADED,
                "message": f"ClamAV unreachable/scan failed, file NOT scanned: {e}",
            })
            context.metadata["virus_scan_passed"] = None
            return context

        status, signature = result.get("stream", (None, None))
        if status == "FOUND":
            raise PipelineError(
                f"Malware detected: {signature}",
                self.name,
                ErrorSeverity.FATAL,
                details={"signature": signature},
            )

        context.metadata["virus_scan_passed"] = True
        return context
