import uuid
from app.engines.base import EngineContext, EngineStatus
from app.engines.classification.manager import ClassificationEngine
from app.engines.ocr.models import OCRResult, OCRPage, OCRBlock, OCRLine, OCRWord, BoundingBox
from app.engines.layout.models import LayoutAnalysisResult, LayoutDocument, LayoutPage, TableRegion, SignatureRegion, StampRegion


def test_classification_engine():
    engine = ClassificationEngine()
    
    # 1. Create Mock OCR Result
    word1 = OCRWord(
        text="CERTIFICAT", confidence=0.9,
        bbox=BoundingBox(x_min=0.1, y_min=0.1, x_max=0.2, y_max=0.15), engine_name="mock"
    )
    word2 = OCRWord(
        text="MÉDICAL", confidence=0.9,
        bbox=BoundingBox(x_min=0.25, y_min=0.1, x_max=0.4, y_max=0.15), engine_name="mock"
    )
    line = OCRLine(words=[word1, word2], bbox=BoundingBox(x_min=0.1, y_min=0.1, x_max=0.4, y_max=0.15))
    block = OCRBlock(lines=[line], bbox=BoundingBox(x_min=0.1, y_min=0.1, x_max=0.4, y_max=0.15))
    ocr_page = OCRPage(blocks=[block])
    ocr_result = OCRResult(page=ocr_page, confidence_score=0.95)
    
    # 2. Create Mock Layout Result
    layout_page = LayoutPage(
        width=1000, height=1000,
        tables=[TableRegion(bounding_box=BoundingBox(x_min=0, y_min=0, x_max=1, y_max=1))],
        signatures=[SignatureRegion(bounding_box=BoundingBox(x_min=0, y_min=0, x_max=1, y_max=1))],
        stamps=[StampRegion(bounding_box=BoundingBox(x_min=0, y_min=0, x_max=1, y_max=1))]
    )
    layout_doc = LayoutDocument(pages=[layout_page])
    layout_result = LayoutAnalysisResult(document=layout_doc)
    
    # 3. Process
    context = EngineContext(
        claim_id=uuid.uuid4(),
        input_data={
            "ocr_result": ocr_result,
            "layout_result": layout_result
        }
    )
    
    result = engine.process(context)
    
    # 4. Assertions
    assert result.status == EngineStatus.SUCCESS
    assert "classification_result" in result.output_data
    
    data = result.output_data["classification_result"]
    assert len(data["documents"]) == 1
    
    doc = data["documents"][0]
    assert doc["classification"]["document_class"]["family"] == "Medical Certificate"
    # Should combine rules and visual classifier predictions
    assert "rules_classifier" in doc["classification"]["engines_used"]
