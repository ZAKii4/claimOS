from app.engines.classification.models import (
    ClassificationPrediction,
    DocumentClass,
    DocumentClassificationResult,
    LogicalDocument,
)
from app.engines.extraction.extractors.insurance.national_id import NationalIdExtractor
from app.engines.extraction.extractors.insurance.owner_identity import OwnerNameExtractor
from app.engines.extraction.extractors.vehicle.vehicle_brand import VehicleBrandExtractor
from app.engines.layout.models import BoundingBox, LayoutAnalysisResult, LayoutDocument, LayoutPage
from app.engines.ocr.models import OCRBlock, OCRLine, OCRPage, OCRResult, OCRWord


def _ocr_for_line(text: str) -> OCRResult:
    bbox = BoundingBox(x_min=0.1, y_min=0.1, x_max=0.5, y_max=0.15)
    words = [
        OCRWord(text=t, confidence=0.9, bbox=bbox, engine_name="test") for t in text.split(" ")
    ]
    line = OCRLine(words=words, bbox=bbox)
    block = OCRBlock(lines=[line], bbox=bbox)
    return OCRResult(page=OCRPage(blocks=[block]), confidence_score=0.9)


def _empty_layout_and_classification():
    page = LayoutPage(width=1000, height=1000)
    layout = LayoutAnalysisResult(document=LayoutDocument(pages=[page]))
    doc_class = DocumentClass(family="Vehicle Registration")
    classification = DocumentClassificationResult(
        documents=[
            LogicalDocument(
                document_index=0,
                page_indices=[0],
                classification=ClassificationPrediction(document_class=doc_class, confidence=0.9),
            )
        ],
        global_confidence=0.9,
    )
    return layout, classification


def test_national_id_extractor_matches_cnie_pattern():
    ocr = _ocr_for_line("Numero CNIE : BE865779")
    layout, classification = _empty_layout_and_classification()

    entities = NationalIdExtractor().extract(ocr, layout, classification)

    assert len(entities) == 1
    assert entities[0].field_name == "national_id"
    assert entities[0].normalized_value == "BE865779"
    assert entities[0].confidence > 0.4


def test_national_id_extractor_finds_nothing_without_pattern():
    ocr = _ocr_for_line("Marque KYMCO")
    layout, classification = _empty_layout_and_classification()

    entities = NationalIdExtractor().extract(ocr, layout, classification)

    assert entities == []


def test_owner_name_extractor_matches_label_value_line():
    ocr = _ocr_for_line("Nom: DUPONT")
    layout, classification = _empty_layout_and_classification()

    entities = OwnerNameExtractor().extract(ocr, layout, classification)

    assert len(entities) == 1
    assert entities[0].field_name == "owner_name"
    assert entities[0].normalized_value == "DUPONT"


def test_vehicle_brand_extractor_matches_label_value_line():
    ocr = _ocr_for_line("Marque: KYMCO")
    layout, classification = _empty_layout_and_classification()

    entities = VehicleBrandExtractor().extract(ocr, layout, classification)

    assert len(entities) == 1
    assert entities[0].field_name == "vehicle_brand"
    assert entities[0].normalized_value == "KYMCO"
