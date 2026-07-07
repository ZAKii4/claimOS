"""
Unit tests for Hybrid OCR Engine.
"""

import os
import tempfile
import uuid

import cv2
import numpy as np

from app.engines.base import EngineContext, EngineStatus
from app.engines.ocr.adapters.mock_adapter import MockOCRAdapter
from app.engines.ocr.engine import HybridOCREngine


def test_mock_adapter():
    adapter = MockOCRAdapter()
    
    img = np.ones((100, 100, 3), dtype=np.uint8)
    
    page = adapter.process(img)
    
    assert page.engine_name == "mock_ocr"
    assert len(page.blocks) == 1
    assert len(page.blocks[0].lines) == 1
    assert len(page.blocks[0].lines[0].words) == 2
    
    word = page.blocks[0].lines[0].words[0]
    assert word.text == "SYNTHETIC"
    assert word.confidence == 0.99


def test_hybrid_ocr_engine():
    engine = HybridOCREngine()
    
    fd, path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    
    img = np.ones((500, 500, 3), dtype=np.uint8) * 255
    # Write some actual text for Tesseract to try if installed
    cv2.putText(img, "HELLO WORLD", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.imwrite(path, img)
    
    context = EngineContext(
        claim_id=uuid.uuid4(),
        input_data={
            "image_path": path,
            "engine_preference": ["mock"] # Force mock for consistent tests
        }
    )
    
    result = engine.process(context)
    
    assert result.status == EngineStatus.SUCCESS
    assert "page" in result.output_data
    
    page = result.output_data["page"]
    assert page["engine_name"] == "mock_ocr"
    
    assert "confidence_score" in result.output_data
    assert result.output_data["confidence_score"] > 0.9 # Mock returns 0.99 and 0.95
    
    os.remove(path)
