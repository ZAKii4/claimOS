import json
from unittest.mock import AsyncMock, MagicMock

from app.engines.classification.models import (
    ClassificationPrediction,
    DocumentClass,
    DocumentClassificationResult,
    LogicalDocument,
)
from app.engines.extraction.extractors.llm.llm_field_extractor import LLMFieldExtractor
from app.engines.layout.models import LayoutAnalysisResult, LayoutDocument, LayoutPage
from app.engines.ocr.models import BoundingBox, OCRBlock, OCRLine, OCRPage, OCRResult, OCRWord
from app.llm.models import LLMResponse, Message, TokenUsage, CostMetrics


def _ocr_result(text: str) -> OCRResult:
    words = [
        OCRWord(text=w, confidence=0.9, bbox=BoundingBox(x_min=0, y_min=0, x_max=1, y_max=1), engine_name="test")
        for w in text.split()
    ]
    line = OCRLine(words=words, bbox=BoundingBox(x_min=0, y_min=0, x_max=1, y_max=1))
    block = OCRBlock(lines=[line], bbox=BoundingBox(x_min=0, y_min=0, x_max=1, y_max=1))
    return OCRResult(page=OCRPage(blocks=[block]), confidence_score=0.9)


def _classification() -> DocumentClassificationResult:
    logical_doc = LogicalDocument(
        document_index=0,
        page_indices=[0],
        classification=ClassificationPrediction(
            document_class=DocumentClass(family="Police Report"), confidence=0.9
        ),
    )
    return DocumentClassificationResult(documents=[logical_doc], global_confidence=0.9)


def _mock_llm_response(payload: dict) -> LLMResponse:
    return LLMResponse(
        id="test",
        provider_name="Ollama",
        model="qwen2.5",
        choices=[Message(role="assistant", content=json.dumps(payload))],
        usage=TokenUsage(),
        cost=CostMetrics(),
        latency_ms=1,
    )


def test_extracts_scalar_fields_from_mocked_llm_response():
    payload = {
        "fields": {
            "date_survenance": {"value": "2026-07-10", "confidence": 0.9},
            "lieu_survenance": {"value": "Casablanca", "confidence": 0.8},
            "sinistre_suspicieux": {"value": False, "confidence": 0.7},
            "responsabilite_pct": {"value": 50, "confidence": 0.6},
        },
        "victimes": [],
    }
    mock_manager = MagicMock()
    mock_manager.generate = AsyncMock(return_value=_mock_llm_response(payload))

    extractor = LLMFieldExtractor(llm_manager=mock_manager)
    entities = extractor.extract(_ocr_result("some real ocr text"), LayoutAnalysisResult(document=LayoutDocument(pages=[LayoutPage(width=1, height=1)])), _classification())

    by_field = {e.field_name: e for e in entities}
    assert by_field["date_survenance"].normalized_value == "2026-07-10"
    assert by_field["lieu_survenance"].normalized_value == "Casablanca"
    assert by_field["sinistre_suspicieux"].normalized_value is False
    assert by_field["responsabilite_pct"].normalized_value == 50.0
    assert all(e.provenance.extraction_method == "llm" for e in entities)


def test_null_fields_produce_no_entities():
    payload = {"fields": {"date_survenance": {"value": None, "confidence": 0.0}}, "victimes": []}
    mock_manager = MagicMock()
    mock_manager.generate = AsyncMock(return_value=_mock_llm_response(payload))

    extractor = LLMFieldExtractor(llm_manager=mock_manager)
    entities = extractor.extract(_ocr_result("text"), LayoutAnalysisResult(document=LayoutDocument(pages=[LayoutPage(width=1, height=1)])), _classification())

    assert entities == []


def test_extracts_victim_list_entities():
    payload = {
        "fields": {},
        "victimes": [
            {"nom": "DUPONT", "prenom": "Jean", "accident_travail": True},
            {"nom": "DURAND", "prenom": "Marie"},
        ],
    }
    mock_manager = MagicMock()
    mock_manager.generate = AsyncMock(return_value=_mock_llm_response(payload))

    extractor = LLMFieldExtractor(llm_manager=mock_manager)
    entities = extractor.extract(_ocr_result("text"), LayoutAnalysisResult(document=LayoutDocument(pages=[LayoutPage(width=1, height=1)])), _classification())

    by_field = {e.field_name: e.normalized_value for e in entities}
    assert by_field["victime.0.nom"] == "DUPONT"
    assert by_field["victime.0.prenom"] == "Jean"
    assert by_field["victime.0.accident_travail"] is True
    assert by_field["victime.1.nom"] == "DURAND"


def test_llm_failure_degrades_to_empty_list_not_crash():
    mock_manager = MagicMock()
    mock_manager.generate = AsyncMock(side_effect=RuntimeError("Ollama unreachable"))

    extractor = LLMFieldExtractor(llm_manager=mock_manager)
    entities = extractor.extract(_ocr_result("text"), LayoutAnalysisResult(document=LayoutDocument(pages=[LayoutPage(width=1, height=1)])), _classification())

    assert entities == []


def test_empty_ocr_text_skips_llm_call_entirely():
    mock_manager = MagicMock()
    mock_manager.generate = AsyncMock()

    extractor = LLMFieldExtractor(llm_manager=mock_manager)
    empty_ocr = OCRResult(page=OCRPage(blocks=[]), confidence_score=0.0)
    entities = extractor.extract(empty_ocr, LayoutAnalysisResult(document=LayoutDocument(pages=[LayoutPage(width=1, height=1)])), _classification())

    assert entities == []
    mock_manager.generate.assert_not_called()
