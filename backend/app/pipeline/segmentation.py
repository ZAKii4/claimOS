"""
Multi-document segmentation.

A single uploaded file (one PDF) can contain several distinct, unrelated
scanned documents back to back — e.g. a police PV, followed by an
insurance attestation, followed by a medical certificate. Classification
already runs per page, but until now the whole file was persisted as one
``ClaimDocument`` row stamped with whichever family the *first* page
happened to get — every other document glued into the same file was
silently mislabeled and never routed to its own extractors.

This module groups a file's already-classified pages into contiguous
logical sub-documents so the caller (``DocumentService``) can persist one
``ClaimDocument`` row per sub-document instead of one per upload.
"""

from dataclasses import dataclass, field

from app.engines.base import EngineStatus
from app.pipeline.core import PageContext

UNKNOWN_FAMILY = "UNKNOWN_DOCUMENT"


@dataclass
class DocumentSegment:
    """One contiguous run of pages recognized as the same logical document."""

    page_numbers: list[int] = field(default_factory=list)
    document_type_code: str = UNKNOWN_FAMILY
    confidence: float = 0.0


def _page_classification(page: PageContext) -> tuple[str, float]:
    """Reads the family/confidence a page's classification step already computed."""
    result = page.engine_results.get("classification")
    if not result or result.status != EngineStatus.SUCCESS:
        return UNKNOWN_FAMILY, 0.0

    classification_result = result.output_data.get("classification_result") or {}
    documents = classification_result.get("documents") or []
    if not documents:
        return UNKNOWN_FAMILY, 0.0

    classification = documents[0].get("classification") or {}
    family = (classification.get("document_class") or {}).get("family") or UNKNOWN_FAMILY
    confidence = classification.get("confidence", 0.0)
    return family, confidence


def segment_pages(pages: list[PageContext]) -> list[DocumentSegment]:
    """
    Groups pages into contiguous sub-documents by their per-page family.

    A page the classifier couldn't place (UNKNOWN_DOCUMENT — e.g. a hand-drawn
    accident sketch, or a page whose OCR yielded no usable text) extends the
    *previous* segment instead of starting a new, empty one: such pages are
    almost always annexes/exhibits belonging to the document just before them,
    not a document in their own right. A new segment only opens when a
    *different, recognized* family actually appears.
    """
    if not pages:
        return []

    runs: list[list[tuple[int, str, float]]] = []
    for page in pages:
        family, confidence = _page_classification(page)
        entry = (page.page_number, family, confidence)
        if runs and (family == UNKNOWN_FAMILY or family == runs[-1][0][1]):
            runs[-1].append(entry)
        else:
            runs.append([entry])

    segments = []
    for run in runs:
        dominant_family = next((f for _, f, _ in run if f != UNKNOWN_FAMILY), UNKNOWN_FAMILY)
        matching_confidences = [c for _, f, c in run if f == dominant_family]
        avg_confidence = (
            sum(matching_confidences) / len(matching_confidences) if matching_confidences else 0.0
        )
        segments.append(
            DocumentSegment(
                page_numbers=[p for p, _, _ in run],
                document_type_code=dominant_family,
                confidence=avg_confidence,
            )
        )
    return segments
