import os
import tempfile
import uuid
import cv2
import numpy as np

from app.engines.base import EngineContext, EngineStatus
from app.engines.layout.manager import LayoutEngine
from app.engines.ocr.models import OCRResult, OCRPage, OCRBlock, OCRLine, OCRWord, BoundingBox


def test_layout_engine():
    # 1. Create a dummy image
    engine = LayoutEngine()
    
    fd, path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    
    img = np.ones((500, 500, 3), dtype=np.uint8) * 255
    cv2.imwrite(path, img)
    
    # 2. Create mock OCR Result
    word1 = OCRWord(
        text="Nom:",
        confidence=0.9,
        bbox=BoundingBox(x_min=0.1, y_min=0.1, x_max=0.2, y_max=0.15),
        engine_name="mock"
    )
    word2 = OCRWord(
        text="Dupont",
        confidence=0.9,
        bbox=BoundingBox(x_min=0.25, y_min=0.1, x_max=0.4, y_max=0.15),
        engine_name="mock"
    )
    
    line = OCRLine(words=[word1, word2], bbox=BoundingBox(x_min=0.1, y_min=0.1, x_max=0.4, y_max=0.15))
    block = OCRBlock(lines=[line], bbox=BoundingBox(x_min=0.1, y_min=0.1, x_max=0.4, y_max=0.15))
    page = OCRPage(blocks=[block])
    
    ocr_result = OCRResult(page=page, confidence_score=0.95)
    
    # 3. Create context
    context = EngineContext(
        claim_id=uuid.uuid4(),
        input_data={
            "image_path": path,
            "ocr_result": ocr_result
        }
    )
    
    # 4. Process
    result = engine.process(context)
    
    # 5. Assertions
    assert result.status == EngineStatus.SUCCESS
    assert "layout_analysis_result" in result.output_data
    
    layout_data = result.output_data["layout_analysis_result"]
    assert "document" in layout_data
    
    pages = layout_data["document"]["pages"]
    assert len(pages) == 1
    
    page = pages[0]
    
    # Paragraph should be detected from OCR block
    assert len(page["paragraphs"]) >= 1
    
    # Form detector should pair 'Nom:' and 'Dupont'
    assert len(page["form_fields"]) >= 1
    assert page["form_fields"][0]["label"] == "Nom:"
    assert page["form_fields"][0]["value"] == "Dupont"
    
    os.remove(path)
