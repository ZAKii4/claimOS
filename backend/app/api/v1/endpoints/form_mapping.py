"""
Form Mapping endpoint.

Exposes the FormMappingEngine (app/engines/form_mapping/) over HTTP: given
the extraction results already produced for each document of a claim's
dossier (tagged with their role in the claim), returns the fused, fully
provenanced ClaimOpeningForm.

Note: extraction results are not yet persisted per document anywhere in
the system (see app/engines/extraction/ — results only live in-memory for
the duration of a single pipeline run). Until that persistence layer
exists, the caller is responsible for supplying each document's
ExtractionResult directly in the request body.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.engines.extraction.models import ExtractionResult
from app.engines.form_mapping.manager import DocumentExtraction, DocumentRole, FormMappingEngine
from app.engines.form_mapping.schema import ClaimOpeningForm

router = APIRouter(prefix="/form-mapping", tags=["Form Mapping"])


class DocumentExtractionRequest(BaseModel):
    document_id: str
    role: DocumentRole
    extraction_result: ExtractionResult


class FormMappingRequest(BaseModel):
    documents: list[DocumentExtractionRequest]


@router.post("/map", response_model=ClaimOpeningForm)
def map_form(request: FormMappingRequest) -> ClaimOpeningForm:
    """Fuses per-document extraction results into the claim opening form."""
    documents = [
        DocumentExtraction(document_id=d.document_id, role=d.role, result=d.extraction_result)
        for d in request.documents
    ]
    return FormMappingEngine().map(documents)
