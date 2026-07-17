"""
Document service — runs the real document processing pipeline for a claim
and persists its result, then fuses persisted documents into a claim
opening form.

This is the first caller that connects three previously-orphaned pieces:
``get_document_pipeline()`` (built and tested, but never invoked outside a
manual script), ``ClaimDocument`` persistence (a repository existed, but
nothing ever constructed a row), and ``FormMappingEngine`` (unit-tested in
isolation, but never fed real per-claim data).
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.engines.base import EngineStatus
from app.engines.evidence_graph.models import EvidenceGraphResult
from app.engines.extraction.merge import merge_document_extraction
from app.engines.extraction.models import ExtractionResult
from app.engines.form_mapping.manager import (
    DocumentExtraction,
    DocumentRole,
    FormMappingEngine,
    infer_document_role,
)
from app.engines.form_mapping.schema import ClaimOpeningForm, FieldSource, FieldStatus, MappedField
from app.models.document import ClaimDocument, DocumentPage
from app.models.operator import Operator
from app.pipeline import DocumentContext, PipelineError, get_document_pipeline
from app.pipeline.core import PageContext
from app.pipeline.segmentation import DocumentSegment, segment_pages
from app.repositories.claim_repository import ClaimRepository
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentIngestRead
from app.services.validation_service import ValidationService
from app.utils.exceptions import BusinessValidationError, EngineProcessingError, EntityNotFoundError

logger = logging.getLogger("claimOS.documents")

_FALLBACK_DOCUMENT_TYPE = "UNKNOWN_DOCUMENT"


class DocumentService:
    """Ingests documents for a claim and maps them into a ClaimOpeningForm."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._claims = ClaimRepository(db)
        self._documents = DocumentRepository(db)
        self._pipeline = get_document_pipeline()
        self._validation = ValidationService(db)

    def ingest_document(
        self,
        claim_id: UUID,
        payload: bytes,
        filename: str,
        content_type: str,
        document_role: DocumentRole | None,
    ) -> list[DocumentIngestRead]:
        """
        Run the real processing pipeline (upload -> ... -> decision) on
        ``payload`` and persist one ``ClaimDocument`` row per logical
        sub-document detected inside it.

        A single uploaded file is frequently a scanned bundle of several
        unrelated documents (e.g. a police PV, an insurance attestation and
        a medical certificate stapled together before scanning) — see
        ``app.pipeline.segmentation``. Persisting the whole upload as one
        row stamped with the first page's classification silently mislabels
        every other document glued into the file. Returns one
        ``DocumentIngestRead`` per detected sub-document (a single-document
        upload still returns a one-item list).

        Raises ``EntityNotFoundError`` if the claim doesn't exist, and
        ``EngineProcessingError`` if the pipeline fails fatally (e.g.
        invalid/corrupt file) — the pipeline's own compensation logic has
        already rolled back any partial side effects by then.
        """
        claim = self._claims.get_by_id(claim_id)
        if claim is None:
            raise EntityNotFoundError("ClaimFile", str(claim_id))

        context = DocumentContext(
            payload=payload,
            filename=filename,
            content_type=content_type,
            claim_id=claim_id,
        )

        try:
            context = self._pipeline.execute(context)
        except PipelineError as e:
            if e.step_name == "upload_and_init":
                # Empty payload / oversized file / unsupported MIME type are
                # client input errors, not an engine failure — surface as a
                # 422 rather than a misleading 502.
                raise BusinessValidationError(e.message) from e
            raise EngineProcessingError(e.step_name, e.message) from e

        segments = segment_pages(context.pages) or [
            DocumentSegment(page_numbers=[p.page_number for p in context.pages] or [1])
        ]

        pipeline_warnings = [e["message"] for e in context.errors]
        pipeline_warnings.extend(self._run_validation(claim_id, context))

        results: list[DocumentIngestRead] = []
        for segment in segments:
            segment_pages_ctx = [p for p in context.pages if p.page_number in segment.page_numbers]
            segment_extracted = {
                str(n): context.extracted_data[str(n)]
                for n in segment.page_numbers
                if str(n) in context.extracted_data
            }
            merged = merge_document_extraction(segment_extracted, segment.document_type_code)
            document_type = self._documents.get_or_create_document_type(
                segment.document_type_code or _FALLBACK_DOCUMENT_TYPE
            )

            # The caller's explicit choice always wins; only fall back to
            # inference (unambiguous families only, e.g. the accident report
            # itself) when nothing was supplied — see infer_document_role().
            effective_role = document_role or infer_document_role(segment.document_type_code)

            document = ClaimDocument(
                claim_id=claim_id,
                document_type_id=document_type.id,
                classification_confidence=Decimal(str(round(segment.confidence, 4))),
                page_range_start=min(segment.page_numbers),
                page_range_end=max(segment.page_numbers),
                storage_uri=context.storage_uri or "",
                document_role=effective_role.value if effective_role else None,
                extracted_data=merged.model_dump(mode="json") if merged else None,
            )
            document = self._documents.create(document)
            self._create_document_pages(document.id, segment_pages_ctx)
            self._db.commit()
            self._db.refresh(document)

            results.append(
                DocumentIngestRead(
                    id=document.id,
                    claim_id=document.claim_id,
                    document_type=document_type.label_fr,
                    document_role=effective_role,
                    classification_confidence=document.classification_confidence,
                    page_range_start=document.page_range_start,
                    page_range_end=document.page_range_end,
                    storage_uri=document.storage_uri,
                    created_at=document.created_at,
                    pipeline_warnings=pipeline_warnings,
                )
            )

        return results

    def _run_validation(self, claim_id: UUID, context: DocumentContext) -> list[str]:
        """
        Persists a real ValidationDecision/issues for this claim, using the
        EvidenceGraphResult the pipeline already computed during this
        document's processing (previously discarded — only extraction was
        ever merged/persisted).

        Scope limit: the evidence graph is built per-document, not fused
        across a claim's documents the way FormMappingEngine fuses
        extraction — so the persisted decision reflects the most recently
        ingested document's graph, not a claim-wide view. Documented rather
        than silently implied to be more than it is.
        """
        evidence_graph_result = context.engine_results.get("evidence_graph")
        if not evidence_graph_result or evidence_graph_result.status != EngineStatus.SUCCESS:
            return []

        graph_data = evidence_graph_result.output_data.get("evidence_graph_result")
        if not graph_data:
            return []

        try:
            graph = EvidenceGraphResult(**graph_data)
            self._validation.run_validation(claim_id, graph)
            return []
        except Exception as e:
            logger.warning("Validation run failed for claim %s: %s", claim_id, e)
            return [f"Validation failed to run: {e}"]

    def _create_document_pages(self, document_id: UUID, pages: list[PageContext]) -> None:
        """
        Persists one DocumentPage row per rendered page.

        Previously nothing ever constructed a DocumentPage row anywhere in
        the codebase — per-page rasterization only ever lived in memory on
        PageContext for the duration of a single pipeline run. Pages with
        no rendered image (an upstream step failed for that page) are
        skipped rather than persisted with a fabricated URI.
        """
        for page in pages:
            if not page.image_uri:
                continue

            iqa_result = page.engine_results.get("iqa")
            quality_score = None
            if iqa_result is not None:
                score = iqa_result.output_data.get("overall_quality_score")
                if score is not None:
                    quality_score = Decimal(str(round(score, 4)))

            self._db.add(
                DocumentPage(
                    document_id=document_id,
                    page_number=page.page_number,
                    original_page_number=page.original_page_number,
                    image_uri=page.image_uri,
                    ocr_hocr_uri=page.ocr_hocr_uri,
                    resolution_dpi=page.resolution_dpi,
                    orientation_corrected_deg=page.orientation_corrected_deg,
                    quality_score=quality_score,
                    is_missing_detected=False,
                )
            )

    def list_documents(self, claim_id: UUID) -> list[DocumentIngestRead]:
        """Lists every document ingested for a claim so far, most recent first."""
        claim = self._claims.get_by_id(claim_id)
        if claim is None:
            raise EntityNotFoundError("ClaimFile", str(claim_id))

        documents = self._documents.get_by_claim(claim_id)
        return [
            DocumentIngestRead(
                id=document.id,
                claim_id=document.claim_id,
                document_type=document.document_type.label_fr,
                document_role=DocumentRole(document.document_role) if document.document_role else None,
                classification_confidence=document.classification_confidence,
                page_range_start=document.page_range_start,
                page_range_end=document.page_range_end,
                storage_uri=document.storage_uri,
                created_at=document.created_at,
                pipeline_warnings=[],
            )
            for document in sorted(documents, key=lambda d: d.created_at, reverse=True)
        ]

    def get_opening_form(self, claim_id: UUID) -> ClaimOpeningForm:
        """
        Fuse every role-tagged, extracted document of a claim into one
        ClaimOpeningForm.

        Documents with no ``document_role`` set (not yet triaged by an
        operator) or no ``extracted_data`` (pipeline never reached
        business extraction, e.g. a fatal failure upstream) are skipped —
        their fields simply stay NOT_FOUND rather than raising, since a
        claim opening form is legitimately built incrementally as
        documents come in.
        """
        claim = self._claims.get_by_id(claim_id)
        if claim is None:
            raise EntityNotFoundError("ClaimFile", str(claim_id))

        documents = self._documents.get_by_claim(claim_id)

        extractions: list[DocumentExtraction] = []
        for document in documents:
            if not document.document_role or not document.extracted_data:
                continue
            extractions.append(
                DocumentExtraction(
                    document_id=str(document.id),
                    role=DocumentRole(document.document_role),
                    result=ExtractionResult(**document.extracted_data),
                )
            )

        form = FormMappingEngine().map(extractions)
        self._apply_overrides(form, claim.field_overrides or {})
        return form

    @staticmethod
    def _apply_overrides(form: ClaimOpeningForm, overrides: dict) -> None:
        """
        Applies persisted manual corrections on top of the auto-fused form.

        A correction always wins over any auto-extracted value/conflict —
        it becomes status=FOUND with confidence=1.0 and a source that
        clearly identifies it as a manual correction (not another
        extractor), so the UI can still show *where* a value came from.
        """
        for path, entry in overrides.items():
            try:
                existing = FormMappingEngine.get_field(form, path)
            except AttributeError:
                continue  # schema changed since the correction was saved; skip rather than crash
            if existing is None:
                continue

            FormMappingEngine.set_field(
                form,
                path,
                MappedField(
                    value=entry.get("value"),
                    status=FieldStatus.FOUND,
                    confidence=1.0,
                    source=FieldSource(
                        document_id="manual-correction",
                        document_class=None,
                        extraction_method="manual_correction",
                        extractor_name=entry.get("corrected_by"),
                        confidence=1.0,
                        raw_value=str(entry.get("value")) if entry.get("value") is not None else None,
                        extracted_at=entry.get("corrected_at") or datetime.now(timezone.utc).isoformat(),
                    ),
                    alternatives=[existing.source] if existing.source else [],
                ),
            )

    @staticmethod
    def _assert_correctable_path(field_path: str) -> None:
        """
        Raises ``BusinessValidationError`` if ``field_path`` doesn't resolve
        to a real MappedField on the schema (typo, or a list path like
        'victimes.0.nom' — not supported yet, see module docstring).
        """
        try:
            target = FormMappingEngine.get_field(ClaimOpeningForm(), field_path)
        except AttributeError:
            target = None
        if target is None:
            raise BusinessValidationError(
                f"'{field_path}' is not a correctable field on ClaimOpeningForm "
                "(unknown path, or a list item such as 'victimes.0.nom')."
            )

    def correct_field(
        self, claim_id: UUID, field_path: str, value: object, operator: Operator
    ) -> ClaimOpeningForm:
        """
        Persists a manual correction for one ClaimOpeningForm field and
        returns the form recomputed with it applied. Thin wrapper around
        ``submit_manual_fields`` for the single-field case (PATCH endpoint).
        """
        return self.submit_manual_fields(claim_id, {field_path: value}, operator)

    def submit_manual_fields(
        self, claim_id: UUID, fields: dict[str, object], operator: Operator
    ) -> ClaimOpeningForm:
        """
        Persists manual values for one or more ClaimOpeningForm fields in a
        single transaction and returns the form recomputed with them applied.

        This is the same mechanism as a single-field correction
        (``field_overrides`` on ``ClaimFile``, always wins over auto-extracted
        values) applied in bulk — it's what lets an operator open a claim
        entirely by hand, without any uploaded document, by submitting every
        known field at once instead of one PATCH per field.

        Raises ``BusinessValidationError`` (naming every offending path) if
        any ``field_path`` doesn't resolve to a real MappedField — the whole
        batch is rejected rather than partially applied, so a typo in one
        field can't silently leave the rest half-saved.
        """
        claim = self._claims.get_by_id(claim_id)
        if claim is None:
            raise EntityNotFoundError("ClaimFile", str(claim_id))

        if not fields:
            raise BusinessValidationError("No fields supplied.")

        invalid_paths = []
        for field_path in fields:
            try:
                self._assert_correctable_path(field_path)
            except BusinessValidationError:
                invalid_paths.append(field_path)
        if invalid_paths:
            raise BusinessValidationError(
                "The following fields are not correctable on ClaimOpeningForm: "
                f"{', '.join(sorted(invalid_paths))}"
            )

        now = datetime.now(timezone.utc).isoformat()
        overrides = dict(claim.field_overrides or {})
        for field_path, value in fields.items():
            overrides[field_path] = {
                "value": value,
                "corrected_by": operator.full_name,
                "corrected_at": now,
            }
        claim.field_overrides = overrides
        self._db.add(claim)
        self._db.commit()

        return self.get_opening_form(claim_id)
