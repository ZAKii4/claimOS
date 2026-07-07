import uuid

from app.engines.base import EngineContext, EngineStatus
from app.engines.classification.models import DocumentClassificationResult, LogicalDocument, ClassificationPrediction, DocumentClass
from app.engines.extraction.manager import ExtractionEngine
from app.engines.extraction.registry import ExtractorRegistry
from app.engines.extraction.extractors.vehicle.license_plate import LicensePlateExtractor
from app.engines.extraction.extractors.insurance.policy_number import PolicyNumberExtractor
from app.engines.layout.models import LayoutAnalysisResult, LayoutDocument, LayoutPage, FormFieldRegion, BoundingBox
from app.engines.ocr.models import OCRResult, OCRPage, OCRBlock, OCRLine, OCRWord


def test_extraction_engine():
    registry = ExtractorRegistry()
    registry.register(LicensePlateExtractor)
    registry.register(PolicyNumberExtractor)
    engine = ExtractionEngine(registry=registry)
    
    # 1. Create Mock OCR Result for License Plate (Regex)
    word1 = OCRWord(text="AB-123-CD", confidence=0.9, bbox=BoundingBox(x_min=0.1, y_min=0.1, x_max=0.2, y_max=0.15), engine_name="mock")
    line = OCRLine(words=[word1], bbox=BoundingBox(x_min=0.1, y_min=0.1, x_max=0.2, y_max=0.15))
    block = OCRBlock(lines=[line], bbox=BoundingBox(x_min=0.1, y_min=0.1, x_max=0.2, y_max=0.15))
    ocr_page = OCRPage(blocks=[block])
    ocr_result = OCRResult(page=ocr_page, confidence_score=0.95)
    
    # 2. Create Mock Layout Result for Policy Number (Form Field)
    form_field = FormFieldRegion(
        bounding_box=BoundingBox(x_min=0.5, y_min=0.5, x_max=0.8, y_max=0.6),
        label_text="N° Police :",
        value_text="AXA1234567"
    )
    layout_page = LayoutPage(width=1000, height=1000, form_fields=[form_field])
    layout_doc = LayoutDocument(pages=[layout_page])
    layout_result = LayoutAnalysisResult(document=layout_doc)
    
    # 3. Create Mock Classification Result
    doc_class = DocumentClass(family="Constat Amiable")
    logical_doc = LogicalDocument(
        document_index=0,
        page_indices=[0],
        classification=ClassificationPrediction(document_class=doc_class, confidence=0.95)
    )
    classification_result = DocumentClassificationResult(
        documents=[logical_doc],
        global_confidence=0.95
    )
    
    # 4. Process
    context = EngineContext(
        claim_id=uuid.uuid4(),
        input_data={
            "ocr_result": ocr_result,
            "layout_result": layout_result,
            "classification_result": classification_result
        }
    )
    
    result = engine.process(context)
    
    # 5. Assertions
    if result.status != EngineStatus.SUCCESS:
        print(f"Engine failed with errors: {result.errors}")
    assert result.status == EngineStatus.SUCCESS
    assert "extraction_result" in result.output_data
    
    data = result.output_data["extraction_result"]
    assert len(data["groups"]) == 1
    
    entities = data["groups"][0]["entities"]
    assert len(entities) == 2
    
    field_names = [e["field_name"] for e in entities]
    assert "vehicle_plate" in field_names
    assert "policy_number" in field_names
    
    plate_entity = next(e for e in entities if e["field_name"] == "vehicle_plate")
    assert plate_entity["normalized_value"] == "AB123CD"
    assert plate_entity["provenance"]["extractor_name"] == "vehicle.license_plate_extractor"
    
    policy_entity = next(e for e in entities if e["field_name"] == "policy_number")
    assert policy_entity["normalized_value"] == "AXA1234567"
    assert policy_entity["provenance"]["extractor_name"] == "insurance.policy_number_extractor"
