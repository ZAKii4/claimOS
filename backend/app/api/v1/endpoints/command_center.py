from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Any

from app.api.v1.dependencies import get_metrics_service
from app.services.metrics_service import MetricsService
from app.command_center.awareness import SituationAwarenessEngine
from app.command_center.decision_room import DecisionRoomEngine
from app.command_center.recommendation import StrategicRecommendationEngine
from app.command_center.kpi import ExecutiveKPIEngine
from app.command_center.scenario import ScenarioPlanningEngine
from app.command_center.reporting import ExecutiveReportingEngine

router = APIRouter(prefix="/command-center", tags=["Command Center & Executive Operations"])

class CreateRoomReq(BaseModel):
    name: str
    topic: str

_KPI_DATA_SOURCE_NOTE = (
    "kpis.business.claims_processed/fraud_prevented_value/automation_rate are "
    "real (from MetricsService); all other KPI fields are illustrative."
)

@router.get("/overview")
def get_overview(metrics_service: MetricsService = Depends(get_metrics_service)):
    kpis = ExecutiveKPIEngine.get_kpis()
    real_metrics = metrics_service.get_dashboard_metrics()

    # Inject real data into KPIs
    kpis["business"]["claims_processed"] = real_metrics["claims_processed"]
    kpis["business"]["fraud_prevented_value"] = f"{real_metrics['fraud_prevented']} €"
    kpis["business"]["automation_rate"] = f"{real_metrics['automation_rate']}%"

    return {
        "kpis": kpis,
        "situation": SituationAwarenessEngine.get_situation(),
        "recommendations": StrategicRecommendationEngine.get_strategic_recommendations(),
        "_data_source": {
            "kpis": _KPI_DATA_SOURCE_NOTE,
            "situation": "illustrative",
            "recommendations": "illustrative",
        },
    }

@router.get("/kpis")
def get_kpis(metrics_service: MetricsService = Depends(get_metrics_service)):
    kpis = ExecutiveKPIEngine.get_kpis()
    real_metrics = metrics_service.get_dashboard_metrics()
    kpis["business"]["claims_processed"] = real_metrics["claims_processed"]
    kpis["business"]["fraud_prevented_value"] = f"{real_metrics['fraud_prevented']} €"
    kpis["business"]["automation_rate"] = f"{real_metrics['automation_rate']}%"
    kpis["_data_source"] = _KPI_DATA_SOURCE_NOTE
    return kpis

@router.get("/recommendations")
def get_recommendations():
    return {
        "recommendations": StrategicRecommendationEngine.get_strategic_recommendations(),
        "_data_source": "illustrative",
    }

@router.get("/decision-rooms")
def get_decision_rooms():
    return DecisionRoomEngine.get_all_rooms()

@router.post("/decision-rooms")
def create_decision_room(req: CreateRoomReq):
    return DecisionRoomEngine.create_room(req.name, req.topic)

@router.get("/situation")
def get_situation():
    return {
        "situation": SituationAwarenessEngine.get_situation(),
        "_data_source": "illustrative",
    }

@router.get("/reports")
def generate_report(type: str = "Board"):
    return ExecutiveReportingEngine.generate_report(type)

@router.get("/scenarios")
def simulate_scenario(scenario: str):
    return ScenarioPlanningEngine.run_simulation(scenario)

@router.get("/operations")
def get_operations():
    return {"status": "ALL_SYSTEMS_NOMINAL", "_data_source": "illustrative"}

@router.get("/executive-dashboard")
def get_executive_dashboard(metrics_service: MetricsService = Depends(get_metrics_service)):
    return get_overview(metrics_service)

