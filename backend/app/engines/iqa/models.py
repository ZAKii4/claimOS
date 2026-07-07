"""
Pydantic DTOs for the Image Quality Assessment Engine.
"""

from pydantic import BaseModel, Field


class ImageQualityReport(BaseModel):
    """
    Comprehensive report on the quality of a single document page image.
    This is embedded in the PageContext.
    """
    estimated_dpi: int | None = Field(default=None, description="Estimated DPI (e.g. 300, 150)")
    
    # Core Quality Metrics
    noise_level: float = Field(default=0.0, description="Noise estimate (0.0 to 1.0, higher is noisier)")
    blur_level: float = Field(default=0.0, description="Variance of Laplacian (lower is blurrier)")
    is_blurred: bool = Field(default=False, description="True if blur_level < threshold")
    contrast: float = Field(default=0.0, description="RMS contrast value")
    brightness: float = Field(default=0.0, description="Mean pixel intensity (0-255)")
    
    # Geometric Metrics
    deskew_angle: float = Field(default=0.0, description="Estimated skew angle in degrees (-45.0 to 45.0)")
    rotation: int = Field(default=0, description="Rotation needed to normalize (0, 90, 180, 270)")
    
    # Compression/File Properties
    jpeg_compression_ratio: float | None = Field(default=None, description="Estimated compression ratio if JPEG")
    
    # Content Heuristics
    has_shadows: bool = Field(default=False, description="True if significant non-uniform illumination is detected")
    has_stamps: bool = Field(default=False, description="True if colorful stamps (e.g. blue/red) detected")
    has_signatures: bool = Field(default=False, description="True if signature-like strokes detected")
    has_handwriting: bool = Field(default=False, description="True if handwriting characteristics detected")
    text_density: float = Field(default=0.0, description="Percentage of pixels classified as text (0.0 to 1.0)")
    
    # Overall Score
    overall_quality_score: float = Field(default=1.0, description="Composite score from 0.0 (unusable) to 1.0 (perfect)")
