from fastapi import APIRouter, Response
from typing import Dict, Any

from app.observability.metrics import metrics_manager
from app.observability.health import health_manager
from app.observability.slo import slo_manager
from app.observability.aiops import aiops_engine

router = APIRouter()

@router.get("/metrics")
async def get_metrics():
    # Return Prometheus text format
    return Response(content=metrics_manager.get_metrics_payload(), media_type="text/plain")

@router.get("/health")
async def get_health():
    return health_manager.check_health()

@router.get("/slo")
async def get_slo():
    return slo_manager.get_slo_report()

@router.get("/aiops/anomalies")
async def get_anomalies():
    # Mock current state
    current_state = {
        "avg_latency": 2.5, # triggers latency anomaly
        "vram_utilization": 92 # triggers vram anomaly
    }
    return {"anomalies": aiops_engine.detect_anomalies(current_state)}
    
@router.get("/aiops/capacity")
async def get_capacity():
    return aiops_engine.predict_capacity()
