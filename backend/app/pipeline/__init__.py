"""
Document Processing Pipeline package.
"""

from app.pipeline.core import DocumentContext, ErrorSeverity, PipelineError
from app.pipeline.orchestrator import PipelineOrchestrator

# Import all steps
from app.pipeline.steps.upload import UploadStep
from app.pipeline.steps.validation import StructuralValidationStep
from app.pipeline.steps.fingerprint import FingerprintStep
from app.pipeline.steps.metadata import MetadataExtractionStep
from app.pipeline.steps.virus_scan import VirusScanStep
from app.pipeline.steps.storage import StorageStep
from app.pipeline.steps.page_extraction import PageExtractionStep
from app.pipeline.steps.iqa import IQAAssessmentStep
from app.pipeline.steps.preprocessing import PreprocessingStep
from app.pipeline.steps.ocr import OCRStep
from app.pipeline.steps.layout_analysis import LayoutAnalysisStep
from app.pipeline.steps.classification import ClassificationStep
from app.pipeline.steps.extraction import BusinessExtractionStep
from app.pipeline.steps.evidence_graph import EvidenceGraphStep
from app.pipeline.steps.cross_validation import CrossValidationStep
from app.pipeline.steps.decision_engine import DecisionEngineStep
from app.pipeline.steps.human_review import HumanReviewStep
from app.pipeline.steps.archiving import ArchivingStep


def get_document_pipeline() -> PipelineOrchestrator:
    """
    Factory creating the full Document Processing Pipeline.
    """
    steps = [
        UploadStep(),
        StructuralValidationStep(),
        FingerprintStep(),
        MetadataExtractionStep(),
        VirusScanStep(),
        StorageStep(),
        PageExtractionStep(),
        IQAAssessmentStep(),
        PreprocessingStep(),
        OCRStep(),
        LayoutAnalysisStep(),
        ClassificationStep(),
        BusinessExtractionStep(),
        EvidenceGraphStep(),
        CrossValidationStep(),
        DecisionEngineStep(),
        HumanReviewStep(),
        ArchivingStep(),
    ]
    return PipelineOrchestrator(steps)

__all__ = [
    "DocumentContext",
    "PipelineOrchestrator",
    "PipelineError",
    "ErrorSeverity",
    "get_document_pipeline",
]
