"""
Adaptive Preprocessing Engine implementation.
"""

import os
import time
import uuid

import cv2

from app.engines.base import BaseEngine, EngineContext, EngineResult, EngineStatus
from app.engines.iqa.models import ImageQualityReport
from app.engines.preprocessing.models import PreprocessingReport
from app.engines.preprocessing.strategy import StrategyBuilder


class AdaptivePreprocessingEngine(BaseEngine):
    """
    Applies a dynamic sequence of image processing operations based on IQA metrics
    to optimize an image for OCR.
    """
    
    def __init__(self) -> None:
        self.strategy_builder = StrategyBuilder()

    @property
    def name(self) -> str:
        return "adaptive_preprocessing"

    @property
    def version(self) -> str:
        return "1.0.0"

    def process(self, context: EngineContext) -> EngineResult:
        """
        Expects:
            context.input_data["image_path"]: str
            context.input_data["iqa_report"]: dict (dump of ImageQualityReport)
            context.input_data["output_dir"]: str
        """
        image_path = context.input_data.get("image_path")
        iqa_report_data = context.input_data.get("iqa_report")
        output_dir = context.input_data.get("output_dir", "/tmp")
        
        if not image_path or not os.path.exists(image_path):
            return self._fail(f"Invalid image_path: {image_path}")
            
        if not iqa_report_data:
            return self._fail("Missing IQA report in context.")
            
        try:
            iqa_report = ImageQualityReport(**iqa_report_data)
        except Exception as e:
            return self._fail(f"Invalid IQA report format: {e}")
            
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            return self._fail("Failed to decode image.")
            
        # Build Strategy
        operations = self.strategy_builder.build_strategy(iqa_report)
        
        applied_operations = []
        total_time = 0
        
        # Execute Pipeline
        current_img = image
        for op in operations:
            current_img, record = op.execute(current_img)
            applied_operations.append(record)
            total_time += record.execution_time_ms
            
        # Save output
        filename = os.path.basename(image_path)
        name, ext = os.path.splitext(filename)
        out_filename = f"{name}_preprocessed_{uuid.uuid4().hex[:6]}.png" # Save as PNG to avoid JPEG artifacts
        out_path = os.path.join(output_dir, out_filename)
        
        cv2.imwrite(out_path, current_img)
        
        # Build Report
        report = PreprocessingReport(
            is_blank_page=iqa_report.text_density < 0.001,
            applied_operations=applied_operations,
            total_processing_time_ms=total_time,
            quality_gain_score=len(applied_operations) * 0.1, # Heuristic stub
            output_image_path=out_path
        )
        
        return EngineResult(
            engine_name=self.name,
            engine_version=self.version,
            status=EngineStatus.SUCCESS,
            output_data=report.model_dump(),
            processing_time_ms=total_time
        )

    def _fail(self, message: str) -> EngineResult:
        return EngineResult(
            engine_name=self.name,
            engine_version=self.version,
            status=EngineStatus.FAILURE,
            errors=[message]
        )

    def health_check(self) -> bool:
        return True
