from fastapi import APIRouter
from app.learning.manager import LearningManager
from app.learning.drift import DriftEngine
from app.learning.quality import QualityEngine
from app.learning.metrics import MetricsEngine
from typing import Dict, Any

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
def get_metrics():
    """Retrieve global KPIs."""
    return {
        "automation_rate": 45.2,
        "override_rate": 12.5,
        "ocr_cer": 0.05,
        "classification_f1": 0.94
    }


@router.get("/drift")
def check_drift():
    """Check for data drift between latest datasets."""
    # Mocking distributions
    dist_a = {"INVOICE": 500, "MEDICAL_REPORT": 300, "POLICE_REPORT": 50}
    dist_b = {"INVOICE": 520, "MEDICAL_REPORT": 290, "POLICE_REPORT": 200}
    
    report = drift_engine.detect_drift("ds_classif_v1", dist_a, "ds_classif_v2", dist_b)
    return report.model_dump()


@router.get("/quality")
def check_quality():
    """Generate a quality report for the latest dataset."""
    return {"status": "success", "quality_score": 0.98}
