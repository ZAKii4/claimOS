from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List

from app.analytics.lake.warehouse import AnalyticsWarehouse
from app.analytics.engines.kpi import KPIEngine
from app.analytics.engines.advanced import AdvancedAnalyticsEngine
from app.analytics.engines.fraud import FraudAnalyticsEngine
from app.analytics.engines.prediction import PredictionEngine
from app.analytics.bi.dashboard import DashboardEngine
from app.analytics.bi.reports import ReportEngine
from app.analytics.bi.quality import DataQualityEngine

router = APIRouter(prefix="/analytics", tags=["Enterprise Analytics & BI"])


class ReportReq(BaseModel):
    tenant_id: str
    report_type: str
    format: str = "JSON"


@router.get("/kpis")
def get_kpis(tenant_id: str):
    return {
        "automation_rate": KPIEngine.calculate_automation_rate(tenant_id),
        "avg_processing_time_sec": KPIEngine.calculate_average_processing_time(tenant_id),
        "ocr_accuracy": KPIEngine.calculate_ocr_accuracy(tenant_id),
        "fraud_rate": KPIEngine.calculate_fraud_rate(tenant_id)
    }


@router.get("/dashboards")
def get_dashboards(tenant_id: str):
    return DashboardEngine.get_executive_dashboard(tenant_id)


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
