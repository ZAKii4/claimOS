"""
Unit tests for the Image Quality Assessment Engine.
"""

import os
import tempfile
import uuid

import cv2
import numpy as np
import pytest

from app.engines.base import EngineContext, EngineStatus
from app.engines.iqa.engine import IQAEngine


@pytest.fixture
def clean_image_path():
    """Generates a temporary clean synthetic image."""
    fd, path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    
    img = np.ones((500, 500, 3), dtype=np.uint8) * 255
    cv2.line(img, (50, 100), (400, 100), (0, 0, 0), 2)
    cv2.line(img, (50, 150), (350, 150), (0, 0, 0), 2)
    
    cv2.imwrite(path, img)
    yield path
    os.remove(path)


@pytest.fixture
def blurry_image_path():
    """Generates a blurry synthetic image."""
    fd, path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    
    img = np.ones((500, 500, 3), dtype=np.uint8) * 150
    cv2.line(img, (50, 100), (400, 100), (0, 0, 0), 2)
    img = cv2.GaussianBlur(img, (15, 15), 0)
    
    cv2.imwrite(path, img)
    yield path
    os.remove(path)


def test_iqa_clean_image(clean_image_path):
    engine = IQAEngine()
    context = EngineContext(
        claim_id=uuid.uuid4(),
        input_data={"image_path": clean_image_path}
    )
    
    result = engine.process(context)
    assert result.status == EngineStatus.SUCCESS
    report = result.output_data
    
    assert report["is_blurred"] is False
    assert report["noise_level"] < 0.1
    assert report["overall_quality_score"] > 0.8
    assert report["deskew_angle"] == 0.0


def test_iqa_blurry_image(blurry_image_path):
    engine = IQAEngine()
    context = EngineContext(
        claim_id=uuid.uuid4(),
        input_data={"image_path": blurry_image_path}
    )
    
    result = engine.process(context)
    assert result.status == EngineStatus.SUCCESS
    report = result.output_data
    
    assert report["is_blurred"] is True
    assert report["overall_quality_score"] < 1.0


def test_iqa_missing_image():
    engine = IQAEngine()
    context = EngineContext(
        claim_id=uuid.uuid4(),
        input_data={"image_path": "/tmp/does_not_exist_xyz123.jpg"}
    )
    
    result = engine.process(context)
    assert result.status == EngineStatus.FAILURE
    assert "missing or invalid" in result.errors[0]
