"""
Pydantic DTOs for the Adaptive Preprocessing Engine.
"""

from typing import Any

from pydantic import BaseModel, Field


class OperationRecord(BaseModel):
    """Logs a single operation applied to an image."""
    operation_name: str = Field(..., description="Name of the operation (e.g. 'DeskewOperation')")
    execution_time_ms: int = Field(..., description="Execution time in milliseconds")
    parameters_used: dict[str, Any] = Field(default_factory=dict, description="Parameters like angle, threshold value, etc.")


class PreprocessingReport(BaseModel):
    """
    Comprehensive report on the preprocessing strategy applied to a single page.
    This is embedded in the PageContext.
    """
    is_blank_page: bool = Field(default=False, description="True if the page was detected as entirely blank")
    applied_operations: list[OperationRecord] = Field(default_factory=list, description="Ordered list of applied operations")
    total_processing_time_ms: int = Field(default=0, description="Total CPU time spent on preprocessing")
    quality_gain_score: float = Field(default=0.0, description="Estimated quality improvement score (heuristic)")
    output_image_path: str = Field(..., description="Path to the optimized output image ready for OCR")
