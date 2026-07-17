from app.engines.classification.models import DocumentClass
from app.engines.extraction.merge import merge_document_extraction
from app.engines.extraction.models import EntityGroup, ExtractedEntity, ExtractionResult, Provenance


def _entity(field_name: str, value: str, confidence: float, page_index: int) -> ExtractedEntity:
    return ExtractedEntity(
        field_name=field_name,
        raw_value=value,
        normalized_value=value,
        entity_type="text",
        confidence=confidence,
        provenance=Provenance(
            page_index=page_index, extractor_name="test.extractor", extraction_method="regex",
        ),
    )


def _page_result(family: str, entities: list[ExtractedEntity]) -> dict:
    return ExtractionResult(
        document_class=DocumentClass(family=family),
        groups=[EntityGroup(group_type="Global", entities=entities)],
        global_confidence=0.8,
        execution_time_ms=10,
        extractors_used=["test.extractor"],
    ).model_dump(mode="json")


def test_merge_returns_none_for_no_pages():
    assert merge_document_extraction({}) is None


def test_merge_concatenates_entities_across_pages_preserving_page_index():
    per_page = {
        "1": _page_result("Vehicle Registration", [_entity("vehicle_plate", "AB-123-CD", 0.9, 0)]),
        "2": _page_result("Vehicle Registration", [_entity("owner_name", "MARTIN", 0.7, 1)]),
    }

    merged = merge_document_extraction(per_page, document_type_code="Vehicle Registration")

    assert merged is not None
    entities = merged.groups[0].entities
    assert {e.field_name for e in entities} == {"vehicle_plate", "owner_name"}
    plate = next(e for e in entities if e.field_name == "vehicle_plate")
    owner = next(e for e in entities if e.field_name == "owner_name")
    assert plate.provenance.page_index == 0
    assert owner.provenance.page_index == 1
    assert merged.document_class.family == "Vehicle Registration"
    assert merged.execution_time_ms == 20
    assert merged.extractors_used == ["test.extractor"]


def test_merge_picks_document_class_matching_document_type_code():
    per_page = {
        "1": _page_result("UNKNOWN_DOCUMENT", []),
        "2": _page_result("Vehicle Registration", [_entity("vehicle_plate", "AB-123-CD", 0.9, 1)]),
    }

    merged = merge_document_extraction(per_page, document_type_code="Vehicle Registration")

    assert merged.document_class.family == "Vehicle Registration"


def test_merge_falls_back_to_first_page_class_when_no_match():
    per_page = {"1": _page_result("Invoice", [])}

    merged = merge_document_extraction(per_page, document_type_code="Nonexistent")

    assert merged.document_class.family == "Invoice"


def test_merge_computes_mean_confidence_over_all_entities():
    per_page = {
        "1": _page_result("Invoice", [_entity("a", "x", 1.0, 0)]),
        "2": _page_result("Invoice", [_entity("b", "y", 0.0, 1)]),
    }

    merged = merge_document_extraction(per_page)

    assert merged.global_confidence == 0.5
