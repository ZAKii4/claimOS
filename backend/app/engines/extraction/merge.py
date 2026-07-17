"""
Merges the per-page ExtractionResult entries the pipeline accumulates on
``DocumentContext.extracted_data`` (keyed by page number) into a single
document-level ExtractionResult, suitable for persisting one row per
document and later feeding into FormMappingEngine.

Each ExtractedEntity already carries its own page_index in its Provenance,
so merging is a plain concatenation — no re-resolution needed here.
Cross-document conflict resolution (same field, different document) is
FormMappingEngine's job; cross-page duplicates within one document are
naturally treated as alternative candidates by the same winner-takes-highest-
confidence logic, since they end up in the same document's entity list.
"""

from app.engines.extraction.models import EntityGroup, ExtractionResult


def merge_document_extraction(
    per_page_results: dict[str, dict],
    document_type_code: str | None = None,
) -> ExtractionResult | None:
    """
    Build one document-level ExtractionResult from per-page result dicts.

    Returns ``None`` if there is nothing to merge (e.g. every page failed
    extraction) — callers should treat that as "no extraction data" rather
    than fabricating an empty-but-present result.
    """
    if not per_page_results:
        return None

    parsed = [ExtractionResult(**data) for data in per_page_results.values()]

    document_class = next(
        (r.document_class for r in parsed if r.document_class.family == document_type_code),
        parsed[0].document_class,
    )

    all_entities = []
    for result in parsed:
        for group in result.groups:
            all_entities.extend(group.entities)
        all_entities.extend(result.loose_entities)

    extractors_used: list[str] = []
    for result in parsed:
        for name in result.extractors_used:
            if name not in extractors_used:
                extractors_used.append(name)

    overall_confidence = (
        sum(e.confidence for e in all_entities) / len(all_entities) if all_entities else 0.0
    )

    return ExtractionResult(
        document_class=document_class,
        groups=[EntityGroup(group_type="Global", entities=all_entities)],
        global_confidence=overall_confidence,
        execution_time_ms=sum(r.execution_time_ms for r in parsed),
        extractors_used=extractors_used,
    )
