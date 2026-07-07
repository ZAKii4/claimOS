"""
Universal Data Models for the Hybrid OCR Engine.
"""

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Normalized bounding box (values between 0.0 and 1.0 based on image width/height)."""
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    @property
    def area(self) -> float:
        return max(0, self.x_max - self.x_min) * max(0, self.y_max - self.y_min)


class OCRWord(BaseModel):
    text: str = Field(..., description="Recognized text string")
    confidence: float = Field(..., description="Confidence score from 0.0 to 1.0")
    bbox: BoundingBox = Field(..., description="Normalized bounding box")
    polygon: list[tuple[float, float]] = Field(default_factory=list, description="List of (x, y) normalized coordinates")
    language: str | None = Field(default=None, description="Detected language, if any")
    engine_name: str = Field(..., description="Name of the OCR engine that produced this word")


class OCRLine(BaseModel):
    words: list[OCRWord]
    bbox: BoundingBox


class OCRBlock(BaseModel):
    lines: list[OCRLine]
    bbox: BoundingBox


class OCRPage(BaseModel):
    blocks: list[OCRBlock]
    language: str | None = None
    engine_name: str | None = None
    processing_time_ms: int = 0


class OCRResult(BaseModel):
    """
    Final output format for the OCR Engine. Embedded into PageContext.
    """
    page: OCRPage
    confidence_score: float = Field(..., description="Global confidence score computed by ConfidenceEngine")
    is_multilingual: bool = False
