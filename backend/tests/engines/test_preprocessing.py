"""
Tests for the Adaptive Preprocessing Engine.
"""

import os
import tempfile
import uuid

import cv2
import numpy as np
import pytest

from app.engines.base import EngineContext, EngineStatus
from app.engines.iqa.models import ImageQualityReport
from app.engines.preprocessing.engine import AdaptivePreprocessingEngine
from app.engines.preprocessing.strategy import StrategyBuilder


@pytest.fixture
def mock_image_path():
    """Generates a temporary synthetic image."""
    fd, path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    
    img = np.ones((500, 500, 3), dtype=np.uint8) * 150
    cv2.line(img, (50, 100), (400, 100), (0, 0, 0), 2)
    cv2.imwrite(path, img)
    
    yield path
    os.remove(path)


def test_strategy_builder_routing():
    builder = StrategyBuilder()
    
    # Clean image report
    clean_report = ImageQualityReport(
        noise_level=0.01, blur_level=500.0, is_blurred=False, contrast=100.0, brightness=200.0,
        deskew_angle=0.0, rotation=0, has_shadows=False, has_stamps=False, has_signatures=False,
        text_density=0.1, overall_quality_score=0.9
    )
    clean_strategy = builder.build_strategy(clean_report)
    
    # Should only have AdaptiveThresholdOperation
    assert len(clean_strategy) == 1
    assert clean_strategy[0].name == "binarize_adaptive"
    
    # Degraded image report
    degraded_report = ImageQualityReport(
        noise_level=0.2, blur_level=10.0, is_blurred=True, contrast=20.0, brightness=100.0,
        deskew_angle=1.5, rotation=90, has_shadows=True, has_stamps=False, has_signatures=False,
        text_density=0.1, overall_quality_score=0.2
    )
    degraded_strategy = builder.build_strategy(degraded_report)
    
    op_names = [op.name for op in degraded_strategy]
    
    assert "rotate" in op_names
    assert "deskew" in op_names
    assert "denoise_nlmeans" in op_names
    assert "sharpen" in op_names
    assert "shadow_removal" in op_names
    assert "clahe" in op_names
    assert "binarize_sauvola" in op_names
    assert "morph_opening" in op_names


def test_preprocessing_engine(mock_image_path):
    engine = AdaptivePreprocessingEngine()
    
    # We will send a degraded IQA report so it tests a few operations
    report = ImageQualityReport(
        noise_level=0.1, blur_level=10.0, is_blurred=True, contrast=20.0, brightness=100.0,
        deskew_angle=0.0, rotation=0, has_shadows=False, has_stamps=False, has_signatures=False,
        text_density=0.1, overall_quality_score=0.5
    )
    
    context = EngineContext(
        claim_id=uuid.uuid4(),
        input_data={
            "image_path": mock_image_path,
            "iqa_report": report.model_dump(),
            "output_dir": "/tmp"
        }
    )
    
    result = engine.process(context)
    
    assert result.status == EngineStatus.SUCCESS
    assert "is_blank_page" in result.output_data
    assert "applied_operations" in result.output_data
    
    ops = result.output_data["applied_operations"]
    assert len(ops) > 0
    
    out_path = result.output_data["output_image_path"]
    assert os.path.exists(out_path)
    
    # Clean up output
    os.remove(out_path)
