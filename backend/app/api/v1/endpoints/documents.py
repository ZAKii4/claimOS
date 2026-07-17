"""
Claim document ingestion endpoints.

Runs the real document processing pipeline (``get_document_pipeline()``)
against an uploaded file, persists the result on ``ClaimDocument``, and
fuses a claim's persisted, role-tagged documents into a ClaimOpeningForm
via ``FormMappingEngine``. Closes the previous gap where the pipeline and
the form-mapping engine were both real but never connected to a claim's
actual, persisted documents (see ``/form-mapping/map`` for the older,
caller-supplies-everything variant).

Two ways to populate a claim's opening form, both converging on the same
``ClaimOpeningForm``/``field_overrides`` mechanism (see docs/COURS_01_DECISIONS_ARCHITECTURE.md
§5): upload documents through this router's ``POST /`` (automatic extraction,
``document_role`` auto-inferred for unambiguous families — docs/COURS_02_ROLE_AUTOMATIQUE.md),
or submit values by hand through ``POST /opening-form/manual`` (bulk manual entry —
docs/COURS_03_SAISIE_MANUELLE.md). ``PATCH /opening-form`` corrects a single field either way.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.v1.dependencies import get_current_operator, get_document_service
from app.engines.form_mapping.manager import DocumentRole
from app.engines.form_mapping.schema import ClaimOpeningForm
from app.models.operator import Operator
from app.schemas.document import (
    DocumentIngestRead,
    FieldCorrectionRequest,
    ManualOpeningFormRequest,
)
from app.services.document_service import DocumentService

router = APIRouter(prefix="/claims/{claim_id}/documents", tags=["Documents"])


@router.post(
    "",
    response_model=list[DocumentIngestRead],
    status_code=201,
    summary="Ingest Document",
    description=(
        "Runs an uploaded file through the real document processing pipeline "
        "(OCR, classification, business extraction, decision) and persists one "
        "ClaimDocument row per logical sub-document detected in the file — a "
        "single upload may be a scanned bundle of several unrelated documents "
        "(e.g. a police PV followed by an insurance attestation). Optionally "
        "tag the document's role (OWN_VEHICLE, ADVERSE_VEHICLE, POLICY_HOLDER, "
        "VICTIM), applied to every sub-document, so it can later be fused into "
        "the claim opening form."
    ),
)
async def ingest_document(
    claim_id: UUID,
    file: UploadFile = File(...),
    document_role: DocumentRole | None = Form(None),
    service: DocumentService = Depends(get_document_service),
    _operator: Operator = Depends(get_current_operator),
) -> list[DocumentIngestRead]:
    payload = await file.read()
    return service.ingest_document(
        claim_id=claim_id,
        payload=payload,
        filename=file.filename or "unknown",
        content_type=file.content_type or "application/octet-stream",
        document_role=document_role,
    )


@router.get(
    "",
    response_model=list[DocumentIngestRead],
    summary="List Claim Documents",
    description="Lists every document ingested for this claim so far, most recent first.",
)
def list_documents(
    claim_id: UUID,
    service: DocumentService = Depends(get_document_service),
    _operator: Operator = Depends(get_current_operator),
) -> list[DocumentIngestRead]:
    return service.list_documents(claim_id)


@router.get(
    "/opening-form",
    response_model=ClaimOpeningForm,
    summary="Get Claim Opening Form",
    description=(
        "Fuses every role-tagged, extracted document ingested for this claim "
        "into one ClaimOpeningForm, with per-field provenance and explicit "
        "NOT_FOUND status for anything the supplied documents don't cover."
    ),
)
def get_opening_form(
    claim_id: UUID,
    service: DocumentService = Depends(get_document_service),
    _operator: Operator = Depends(get_current_operator),
) -> ClaimOpeningForm:
    return service.get_opening_form(claim_id)


@router.patch(
    "/opening-form",
    response_model=ClaimOpeningForm,
    summary="Correct Opening Form Field",
    description=(
        "Manually overrides one field of the fused ClaimOpeningForm (e.g. to "
        "resolve a CONFLICT, fill a NOT_FOUND field, or fix a low-confidence "
        "extraction). The correction always wins over auto-extracted values "
        "and persists across future fetches. Not yet supported for list items "
        "(victimes.<index>.<field>)."
    ),
)
def correct_opening_form_field(
    claim_id: UUID,
    correction: FieldCorrectionRequest,
    service: DocumentService = Depends(get_document_service),
    operator: Operator = Depends(get_current_operator),
) -> ClaimOpeningForm:
    return service.correct_field(claim_id, correction.field_path, correction.value, operator)


@router.post(
    "/opening-form/manual",
    response_model=ClaimOpeningForm,
    summary="Submit Opening Form Manually",
    description=(
        "Registers or completes a claim's opening form entirely by hand — the alternative "
        "to uploading documents when a sinistre is reported without paperwork yet (e.g. "
        "phoned in) or to fill fields no uploaded document covered. Accepts a flat map of "
        "dotted ClaimOpeningForm paths to values in one request; every value is persisted "
        "as a manual correction (status=FOUND, confidence=1.0) with the same precedence "
        "over auto-extracted data as the single-field PATCH endpoint above. The whole "
        "batch is rejected if any field path is invalid, so a typo can't half-save a form."
    ),
)
def submit_opening_form_manually(
    claim_id: UUID,
    payload: ManualOpeningFormRequest,
    service: DocumentService = Depends(get_document_service),
    operator: Operator = Depends(get_current_operator),
) -> ClaimOpeningForm:
    return service.submit_manual_fields(claim_id, payload.fields, operator)
