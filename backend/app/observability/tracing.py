import uuid
import time
from contextvars import ContextVar
from typing import Dict, List, Optional
from app.observability.models import Span, Trace

# Context variables for Distributed Tracing
current_trace_id: ContextVar[str] = ContextVar("current_trace_id", default="")
current_span_id: ContextVar[str] = ContextVar("current_span_id", default="")

class TracingEngine:
    """In-memory trace aggregator."""
    
    _traces: Dict[str, Trace] = {}

    @classmethod
    def start_trace(cls, claim_id: Optional[str] = None) -> str:
        trace_id = str(uuid.uuid4())
        current_trace_id.set(trace_id)
        current_span_id.set("")
        cls._traces[trace_id] = Trace(id=trace_id, claim_id=claim_id, start_time=time.time())
        return trace_id

    @classmethod
    def start_span(cls, name: str, tags: dict = None) -> Span:
        trace_id = current_trace_id.get()
        if not trace_id:
            # Auto-start trace if missing
            trace_id = cls.start_trace()
            
        parent_id = current_span_id.get() or None
        span_id = str(uuid.uuid4())
        
        span = Span(
            id=span_id,
            trace_id=trace_id,
            parent_id=parent_id,
            name=name,
            start_time=time.time(),
            tags=tags or {}
        )
        
        cls._traces[trace_id].spans.append(span)
        current_span_id.set(span_id)
        return span

    @classmethod
    def end_span(cls, span: Span, error: Exception = None):
        span.end_time = time.time()
        span.duration_ms = (span.end_time - span.start_time) * 1000
        if error:
            span.error = str(error)
            
        # Revert context to parent
        current_span_id.set(span.parent_id or "")

    @classmethod
    def get_trace(cls, trace_id: str) -> Optional[Trace]:
        return cls._traces.get(trace_id)
        
    @classmethod
    def get_all_traces(cls) -> List[Trace]:
        return list(cls._traces.values())
