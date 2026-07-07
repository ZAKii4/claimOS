import pytest
import asyncio
from app.observability.tracing import TracingEngine, current_trace_id, current_span_id
from app.observability.decorators import traceable
from app.observability.metrics import MetricsEngine
from app.observability.timeline import TimelineEngine
from app.observability.health import HealthManager
from app.observability.alerts import AlertEngine
from app.observability.profiler import ProfilerEngine
from app.observability.costs import CostEngine


def test_tracing_and_decorators():
    @traceable(name="ParentOp")
    async def parent_op():
        return await child_op()
        
    @traceable(name="ChildOp")
    async def child_op():
        return "Success"
        
    # Reset context before test
    current_trace_id.set("")
    current_span_id.set("")
    
    res = asyncio.run(parent_op())
    assert res == "Success"
    
    traces = TracingEngine.get_all_traces()
    assert len(traces) > 0
    trace = traces[-1]
    
    assert len(trace.spans) == 2
    parent_span = next(s for s in trace.spans if s.name == "ParentOp")
    child_span = next(s for s in trace.spans if s.name == "ChildOp")
    
    assert child_span.parent_id == parent_span.id
    assert parent_span.duration_ms is not None


def test_metrics_engine():
    MetricsEngine.increment("test_counter", 1)
    MetricsEngine.increment("test_counter", 2)
    MetricsEngine.record_latency("test_latency", 10.0)
    MetricsEngine.record_latency("test_latency", 20.0)
    
    summary = MetricsEngine.get_summary()
    assert summary["counters"]["test_counter"] == 3
    assert summary["latencies"]["test_latency"]["avg"] == 15.0


def test_timeline_engine():
    TimelineEngine.record_event("claim123", "UPLOAD", "user")
    TimelineEngine.record_event("claim123", "OCR_DONE", "system")
    
    timeline = TimelineEngine.get_timeline("claim123")
    assert len(timeline) == 2
    assert timeline[0].event_type == "UPLOAD"
    assert timeline[1].event_type == "OCR_DONE"


def test_health_manager():
    manager = HealthManager()
    
    async def run():
        return await manager.check_all()
        
    res = asyncio.run(run())
    assert res["status"] == "GREEN"
    assert len(res["components"]) == 2


def test_alert_engine():
    AlertEngine.check_cpu(98.0)
    alerts = AlertEngine.get_alerts()
    assert len(alerts) > 0
    assert alerts[0].category == "Infrastructure"
    assert "98.0" in alerts[0].message


def test_profiler_and_costs():
    CostEngine.record_cost("OCR", 1.5, "claim123")
    CostEngine.record_cost("LLM", 2.0, "claim123")
    
    summary = CostEngine.get_summary()
    assert summary["total_by_claim"]["claim123"] == 3.5
    assert summary["global_total"] == 3.5
    
    # Test Flame Graph Generation from existing trace if available
    traces = TracingEngine.get_all_traces()
    if traces:
        flame = ProfilerEngine.generate_flame_graph(traces[-1].id)
        assert flame["trace_id"] == traces[-1].id
        assert len(flame["flame_graph"]) == 1 # One root span
