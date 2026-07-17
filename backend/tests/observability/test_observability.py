import json
from app.observability.metrics import metrics_manager
from app.observability.tracing import tracing_manager
from app.observability.logging import logging_manager
from app.observability.health import health_manager
from app.observability.slo import slo_manager
from app.observability.aiops import aiops_engine

def test_metrics_manager():
    # Record a request
    metrics_manager.api_requests.labels(method='GET', endpoint='/test', status='200').inc()
    payload = metrics_manager.get_metrics_payload()
    assert b"claimos_api_requests_total" in payload

def test_tracing_manager():
    trace_id1 = tracing_manager.get_current_trace_id()
    assert len(trace_id1) > 0
    
    with tracing_manager.start_span("test_span", {"custom_attr": "value"}):
        trace_id2 = tracing_manager.get_current_trace_id()
        assert len(trace_id2) > 0

def test_logging_manager(caplog):
    # Using caplog to verify the JSON output
    logging_manager.info("Test message", {"key": "value"})
    assert "Test message" in caplog.text

def test_health_manager():
    health = health_manager.check_health()
    assert "status" in health
    assert "components" in health
    assert health["components"]["postgresql"] == "healthy"

def test_slo_manager():
    report = slo_manager.get_slo_report()
    assert "availability_target" in report
    assert "current_availability" in report
    
    # 1,000,000 requests, 500 failed = 99.95% availability
    assert report["current_availability"] == 99.95
    # Error budget for 99.9% is 1000 failures. 500 failed -> 50% remaining.
    assert round(report["error_budget_remaining_percent"], 2) == 50.0

def test_aiops_engine():
    # Test anomalies
    anomalies = aiops_engine.detect_anomalies({
        "avg_latency": 2.5,
        "vram_utilization": 95
    })
    
    assert len(anomalies) == 2
    types = [a["type"] for a in anomalies]
    assert "latency_spike" in types
    assert "vram_exhaustion_warning" in types
    
    # Test predictions
    preds = aiops_engine.predict_capacity()
    assert "days_until_db_full" in preds
