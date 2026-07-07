from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime


class LearningSample(BaseModel):
    id: str
    claim_id: str
    document_id: Optional[str]
    review_id: str
    task_type: str  # OCR, CLASSIFICATION, EXTRACTION, DECISION
    
    input_data: Dict[str, Any]
    expected_output: Dict[str, Any]
    corrected_output: Dict[str, Any]
    
    confidence: float
    operator: str
    processing_time_ms: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DatasetMetadata(BaseModel):
    dataset_id: str
    version: str
    task_type: str
    hash_signature: str
    creation_date: datetime = Field(default_factory=datetime.utcnow)
    statistics: Dict[str, Any]
    source_reviews: List[str]
    
    
class DatasetQualityReport(BaseModel):
    dataset_id: str
    total_samples: int
    class_distribution: Dict[str, int]
    avg_confidence: float
    invalid_samples: int
    review_coverage_percent: float


class DriftReport(BaseModel):
    dataset_a: str
    dataset_b: str
    kl_divergence: float
    population_stability_index: float
    drift_detected: bool
    drift_details: Dict[str, Any]
