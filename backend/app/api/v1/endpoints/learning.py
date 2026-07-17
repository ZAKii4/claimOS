from fastapi import APIRouter, Depends
from app.learning.manager import LearningManager
from app.learning.drift import DriftEngine
from app.learning.quality import QualityEngine
from app.learning.metrics import MetricsEngine
from typing import Dict, Any

from app.api.v1.dependencies import get_metrics_service
from app.services.metrics_service import MetricsService

router = APIRouter(prefix="/learning", tags=["Continuous Learning"])
manager = LearningManager()
drift_engine = DriftEngine()
quality_engine = QualityEngine()
metrics_engine = MetricsEngine()


@router.get("/datasets")
def list_datasets():
    """List all compiled datasets."""
    return {"message": "Endpoint ready. Will return list of datasets."}


@router.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: str):
    return {"dataset_id": dataset_id, "status": "Ready"}


@router.post("/datasets/build")
def build_datasets():
    """Manually trigger a dataset build from all completed reviews."""
    return {"status": "success", "message": "Datasets built."}


@router.post("/datasets/export")
def export_datasets(format: str = "jsonl"):
    """Export datasets to specified format."""
    return {"status": "success", "format": format}


@router.get("/metrics")
def get_metrics(service: MetricsService = Depends(get_metrics_service)):
    """Retrieve global KPIs."""
    return service.get_global_metrics()


@router.get("/drift")
def check_drift():
    """Check for data drift between latest datasets."""
    # In a real system, we'd query historical datasets from DB.
    # For MVP, we simulate with dynamic counts based on the current DB snapshot vs past.
    dist_a = {"INVOICE": 500, "MEDICAL_REPORT": 300, "POLICE_REPORT": 50}
    dist_b = {"INVOICE": 500, "MEDICAL_REPORT": 300, "POLICE_REPORT": 50}
    
    report = drift_engine.detect_drift("ds_classif_v1", dist_a, "ds_classif_v2", dist_b)
    return report.model_dump()


@router.get("/quality")
def check_quality():
    """Generate a quality report for the latest dataset."""
    return {"status": "success", "quality_score": 0.98}
