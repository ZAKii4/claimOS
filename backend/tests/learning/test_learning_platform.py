import pytest
from app.learning.manager import LearningManager
from app.learning.drift import DriftEngine
from app.learning.models import LearningSample
from app.learning.dataset_versioning import DatasetVersioning
import uuid
from datetime import datetime


def test_feedback_collection_and_building():
    manager = LearningManager()
    
    session_data = {"claim_id": "C-1", "id": "REV-1"}
    audit_logs = [
        {"action": "CORRECTED_CLASS", "actor": "OP-1", "old_value": {"class": "INVOICE"}, "new_value": {"class": "RECEIPT"}},
        {"action": "CORRECTED_BBOX", "actor": "OP-1", "old_value": {"x": 10}, "new_value": {"x": 20}}
    ]
    
    samples = manager.process_review_session(session_data, audit_logs)
    assert len(samples) == 2
    assert samples[0].task_type == "CLASSIFICATION"
    assert samples[1].task_type == "OCR"


def test_drift_detection_pure_python():
    engine = DriftEngine()
    
    # Identical distributions should have 0 kl divergence and 0 psi
    dist_a = {"INVOICE": 500, "MEDICAL": 500}
    dist_b = {"INVOICE": 500, "MEDICAL": 500}
    
    report_identical = engine.detect_drift("ds_1", dist_a, "ds_2", dist_b)
    assert report_identical.drift_detected is False
    assert report_identical.kl_divergence < 0.001
    
    # Drastic shift
    dist_c = {"INVOICE": 10, "MEDICAL": 990}
    report_drift = engine.detect_drift("ds_1", dist_a, "ds_3", dist_c)
    assert report_drift.drift_detected is True
    assert report_drift.population_stability_index > 0.2


def test_dataset_immutability():
    versioning = DatasetVersioning()
    samples = [
        LearningSample(id="1", claim_id="C-1", document_id="D-1", review_id="R-1", task_type="OCR", input_data={}, expected_output={}, corrected_output={"val": 1}, confidence=1.0, operator="SYSTEM", processing_time_ms=0, created_at=datetime.utcnow()),
        LearningSample(id="2", claim_id="C-1", document_id="D-1", review_id="R-1", task_type="OCR", input_data={}, expected_output={}, corrected_output={"val": 2}, confidence=1.0, operator="SYSTEM", processing_time_ms=0, created_at=datetime.utcnow())
    ]
    
    metadata = versioning.create_version("dataset_ocr", "OCR", samples, "v1.0.0")
    
    assert metadata.version == "v1.0.1"
    
    # Test deterministic hash
    metadata2 = versioning.create_version("dataset_ocr", "OCR", samples[::-1], "v1.0.0") # Reverse order shouldn't matter
    assert metadata.hash_signature == metadata2.hash_signature
