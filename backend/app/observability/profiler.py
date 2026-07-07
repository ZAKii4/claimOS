from typing import Dict, Any, List
from app.observability.tracing import TracingEngine, Trace


class ProfilerEngine:
    """Generates logical Flame Graphs from Traces."""
    
    @classmethod
    def generate_flame_graph(cls, trace_id: str) -> Dict[str, Any]:
        trace = TracingEngine.get_trace(trace_id)
        if not trace:
            return {}
            
        # Build hierarchy
        nodes = {span.id: {"name": span.name, "value": span.duration_ms or 0, "children": []} for span in trace.spans}
        roots = []
        
        for span in trace.spans:
            if span.parent_id and span.parent_id in nodes:
                nodes[span.parent_id]["children"].append(nodes[span.id])
            else:
                roots.append(nodes[span.id])
                
        return {
            "trace_id": trace.id,
            "claim_id": trace.claim_id,
            "flame_graph": roots
        }
