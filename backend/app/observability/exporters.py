import json
from app.observability.tracing import TracingEngine


class JsonExporter:
    """Exports traces and metrics to JSON."""
    
    @staticmethod
    def export_trace(trace_id: str) -> str:
        trace = TracingEngine.get_trace(trace_id)
        if not trace:
            return "{}"
        return trace.model_dump_json(indent=2)


class OpenTelemetryExporterStub:
    """
    Stub for future integration with opentelemetry-sdk.
    Keeps dependencies clean for MVP.
    """
    @staticmethod
    def export():
        pass
