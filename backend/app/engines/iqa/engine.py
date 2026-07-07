"""
Image Quality Assessment Engine implementation.
"""

import os

import cv2

from app.engines.base import BaseEngine, EngineContext, EngineResult, EngineStatus
from app.engines.iqa.metrics.blur import BlurAnalyzer
from app.engines.iqa.metrics.content import ContentAnalyzer
from app.engines.iqa.metrics.exposure import ExposureAnalyzer
from app.engines.iqa.metrics.geometry import GeometryAnalyzer
from app.engines.iqa.metrics.noise import NoiseAnalyzer
from app.engines.iqa.models import ImageQualityReport


class IQAEngine(BaseEngine):
    """
    Evaluates the quality of a document page image.
    Uses OpenCV heuristics to compute blur, noise, contrast, and layout markers.
    """
    
    def __init__(self) -> None:
        self.blur_analyzer = BlurAnalyzer()
        self.noise_analyzer = NoiseAnalyzer()
        self.geometry_analyzer = GeometryAnalyzer()
        self.exposure_analyzer = ExposureAnalyzer()
        self.content_analyzer = ContentAnalyzer()

    @property
    def name(self) -> str:
        return "iqa_engine"

    @property
    def version(self) -> str:
        return "1.0.0"

    def process(self, context: EngineContext) -> EngineResult:
        """
        Processes a single image file provided in context.input_data['image_path'].
        """
        image_path = context.input_data.get("image_path")
        
        if not image_path or not os.path.exists(image_path):
            return EngineResult(
                engine_name=self.name,
                engine_version=self.version,
                status=EngineStatus.FAILURE,
                errors=[f"Image path missing or invalid: {image_path}"]
            )
            
        try:
            # Read image
            image_color = cv2.imread(image_path)
            if image_color is None:
                raise ValueError("Failed to decode image file.")
                
            image_gray = cv2.cvtColor(image_color, cv2.COLOR_BGR2GRAY)
            
            # Analyze
            blur_data = self.blur_analyzer.analyze(image_gray)
            noise_data = self.noise_analyzer.analyze(image_gray)
            geom_data = self.geometry_analyzer.analyze(image_gray)
            exp_data = self.exposure_analyzer.analyze(image_gray)
            content_data = self.content_analyzer.analyze(image_color, image_gray)
            
            # Compute overall score (heuristic)
            # A perfect score is 1.0. We penalize for noise, blur, and severe skew.
            score = 1.0
            score -= min(0.5, noise_data["noise_level"] * 5)
            if blur_data["is_blurred"]:
                score -= 0.3
            if abs(geom_data["deskew_angle"]) > 5.0:
                score -= 0.2
            
            overall_quality_score = max(0.0, score)
            
            # Build report
            report = ImageQualityReport(
                blur_level=blur_data["blur_level"],
                is_blurred=blur_data["is_blurred"],
                noise_level=noise_data["noise_level"],
                deskew_angle=geom_data["deskew_angle"],
                rotation=geom_data["rotation"],
                brightness=exp_data["brightness"],
                contrast=exp_data["contrast"],
                has_shadows=exp_data["has_shadows"],
                text_density=content_data["text_density"],
                has_stamps=content_data["has_stamps"],
                has_signatures=content_data["has_signatures"],
                has_handwriting=content_data["has_handwriting"],
                overall_quality_score=overall_quality_score,
                estimated_dpi=context.input_data.get("estimated_dpi")
            )
            
            return EngineResult(
                engine_name=self.name,
                engine_version=self.version,
                status=EngineStatus.SUCCESS,
                output_data=report.model_dump(),
                confidence=overall_quality_score
            )
            
        except Exception as e:
            return EngineResult(
                engine_name=self.name,
                engine_version=self.version,
                status=EngineStatus.FAILURE,
                errors=[f"IQA Engine error: {str(e)}"]
            )

    def health_check(self) -> bool:
        return True
