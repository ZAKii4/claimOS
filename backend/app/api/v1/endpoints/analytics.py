import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.metrics_service import MetricsService
from app.analytics.lake.warehouse import AnalyticsWarehouse
from app.analytics.engines.kpi import KPIEngine
from app.analytics.engines.advanced import AdvancedAnalyticsEngine
from app.analytics.engines.fraud import FraudAnalyticsEngine
from app.analytics.engines.prediction import PredictionEngine
from app.analytics.bi.dashboard import DashboardEngine
from app.analytics.bi.reports import ReportEngine
from app.analytics.bi.quality import DataQualityEngine

router = APIRouter(prefix="/analytics", tags=["Enterprise Analytics & BI"])
logger = logging.getLogger("claimOS.analytics")


class ReportReq(BaseModel):
    tenant_id: str
    report_type: str
    format: str = "JSON"


@router.get("/kpis")
def get_kpis(tenant_id: str, db: Session = Depends(get_db)):
    metrics_svc = MetricsService(db)
    return metrics_svc.get_global_metrics()


@router.get("/dashboards")
def get_dashboards(tenant_id: str, db: Session = Depends(get_db)):
    try:
        metrics_svc = MetricsService(db)
        return metrics_svc.get_dashboard_metrics()
    except Exception as e:
        # Previously masked this failure with hardcoded fake metrics — that
        # hid real DB outages from operators and evaluators alike. Fail
        # loudly instead.
        logger.error("Failed to compute dashboard metrics for tenant %s: %s", tenant_id, e)
        raise HTTPException(status_code=502, detail="Unable to compute dashboard metrics") from e


@router.get("/warehouse")
def get_warehouse_stats(tenant_id: str, fact_type: str):
    agg = AnalyticsWarehouse.query_aggregate(tenant_id, fact_type)
    return agg


@router.get("/fraud")
def get_fraud_analytics(tenant_id: str):
    return {
        "heatmap": FraudAnalyticsEngine.generate_fraud_heatmap(tenant_id),
        "networks": FraudAnalyticsEngine.detect_fraud_network(tenant_id)
    }


@router.get("/predictions")
def get_predictions(tenant_id: str):
    return {
        "volume_forecast_30d": PredictionEngine.forecast_volume(tenant_id),
        "llm_cost_forecast": PredictionEngine.forecast_llm_costs(tenant_id)
    }


@router.get("/trends")
def get_trends(tenant_id: str, fact_type: str, measure: str):
    return {
        "trend_analysis": AdvancedAnalyticsEngine.analyze_trends(tenant_id, fact_type, measure),
        "anomalies": AdvancedAnalyticsEngine.detect_anomalies(tenant_id, fact_type, measure)
    }


@router.get("/quality")
def run_quality_checks(tenant_id: str):
    return DataQualityEngine.run_checks(tenant_id)


@router.post("/reports/generate")
def generate_report(req: ReportReq):
    content = ReportEngine.generate_report(req.tenant_id, req.report_type, req.format)
    return {"status": "generated", "content": content}
