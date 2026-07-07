from fastapi import APIRouter
from app.observability.health import HealthManager
from app.observability.metrics import MetricsEngine
from app.observability.tracing import TracingEngine
from app.observability.alerts import AlertEngine
from app.observability.timeline import TimelineEngine
from app.observability.costs import CostEngine
from app.observability.profiler import ProfilerEngine

router = APIRouter(prefix="/monitoring", tags=["Enterprise Observability"])
health_manager = HealthManager()


@router.get("/health")
async def get_health():
    return await health_manager.check_all()


@router.get("/metrics")
def get_metrics():
    return MetricsEngine.get_summary()


@router.get("/costs")
def get_costs():
    return CostEngine.get_summary()


@router.get("/alerts")
def get_alerts():
    return [a.model_dump() for a in AlertEngine.get_alerts()]


@router.get("/traces/{trace_id}")
def get_trace(trace_id: str):
    return ProfilerEngine.generate_flame_graph(trace_id)


@router.get("/timeline/{claim_id}")
def get_timeline(claim_id: str):
    return [e.model_dump() for e in TimelineEngine.get_timeline(claim_id)]
