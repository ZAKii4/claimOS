"""
End-to-end regression tests for real document ingestion.

Connects the pipeline (real OCR/classification/extraction on a real PDF),
persistence (a ClaimDocument row actually gets written), and the form
mapping engine (fused into a real ClaimOpeningForm) — three pieces that
were each independently real but, before this, never called together.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_session_factory
from app.main import app
from app.models.claim import ClaimFile
from app.models.document import DocumentPage
from app.models.lookups import ClaimType, OperatorRole
from app.models.operator import Operator
from app.security.password_policy import password_policy

client = TestClient(app)

TEST_PASSWORD = "Test-Password-123!"


def _build_synthetic_pdf(marque: str = "TOYOTA", plate: str = "AB-123-CD") -> bytes:
    """A real, valid PDF with claim-like key/value text, rendered via PyMuPDF."""
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), "CONSTAT AMIABLE D'ACCIDENT")
    page.insert_text((50, 110), f"PLATE: {plate}")
    page.insert_text((50, 150), "Nom: MARTIN")
    page.insert_text((50, 190), f"Marque: {marque}")
    page.insert_text((50, 230), "Description: Rear-end collision at a red light.")
    return doc.tobytes()


@pytest.fixture
def auth_headers():
    """Creates a real operator, logs in for real, yields Authorization headers, cleans up."""
    Session = get_session_factory()
    db = Session()
    operator = None
    try:
        role = db.query(OperatorRole).filter(OperatorRole.code == "TEST_ROLE").first()
        if not role:
            role = OperatorRole(code="TEST_ROLE")
            db.add(role)
            db.commit()
            db.refresh(role)

        operator = Operator(
            employee_id=f"TEST-{uuid.uuid4().hex[:8]}",
            full_name="Test Operator",
            email=f"test-{uuid.uuid4().hex[:8]}@example.com",
            role_id=role.id,
            hashed_password=password_policy.get_password_hash(TEST_PASSWORD),
        )
        db.add(operator)
        db.commit()
        db.refresh(operator)

        login = client.post(
            "/api/v1/auth/login",
            json={"email": operator.email, "password": TEST_PASSWORD},
        )
        token = login.json()["access_token"]
        yield {"Authorization": f"Bearer {token}"}
    finally:
        if operator is not None:
            db.query(Operator).filter(Operator.id == operator.id).delete()
            db.commit()
        db.close()


@pytest.fixture
def real_claim(auth_headers):
    Session = get_session_factory()
    db = Session()
    try:
        claim_type = db.query(ClaimType).filter(ClaimType.code == "CAR_ACCIDENT").first()
        assert claim_type is not None, "CAR_ACCIDENT claim type must be seeded"
        claim_type_id = str(claim_type.id)
    finally:
        db.close()

    response = client.post(
        "/api/v1/claims",
        json={
            "external_ref": f"TEST-{uuid.uuid4().hex[:8]}",
            "claim_type_id": claim_type_id,
            "date_of_loss": "2026-07-10",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201, response.text
    claim_id = response.json()["id"]
    try:
        yield claim_id
    finally:
        # ClaimDocument rows cascade-delete with the claim (FK ondelete=CASCADE);
        # only after that can any newly get-or-created DocumentType rows be freed.
        Session = get_session_factory()
        db = Session()
        try:
            db.query(ClaimFile).filter(ClaimFile.id == uuid.UUID(claim_id)).delete()
            db.commit()
        finally:
            db.close()


def test_ingest_document_runs_real_pipeline_and_persists(auth_headers, real_claim):
    payload = _build_synthetic_pdf()

    response = client.post(
        f"/api/v1/claims/{real_claim}/documents",
        files={"file": ("constat.pdf", payload, "application/pdf")},
        data={"document_role": "OWN_VEHICLE"},
        headers=auth_headers,
    )

    assert response.status_code == 201, response.text
    documents = response.json()
    assert len(documents) == 1, "single-page synthetic PDF should yield exactly one sub-document"
    body = documents[0]
    assert body["claim_id"] == real_claim
    assert body["document_role"] == "OWN_VEHICLE"
    assert body["page_range_start"] == 1
    assert body["page_range_end"] == 1
    assert body["storage_uri"].startswith("local://")

    Session = get_session_factory()
    db = Session()
    try:
        pages = db.query(DocumentPage).filter(DocumentPage.document_id == uuid.UUID(body["id"])).all()
        assert len(pages) == 1
        assert pages[0].page_number == 1
        assert pages[0].image_uri
    finally:
        db.close()


def test_list_documents_returns_ingested_documents(auth_headers, real_claim):
    payload = _build_synthetic_pdf()
    upload_response = client.post(
        f"/api/v1/claims/{real_claim}/documents",
        files={"file": ("constat.pdf", payload, "application/pdf")},
        data={"document_role": "OWN_VEHICLE"},
        headers=auth_headers,
    )
    assert upload_response.status_code == 201, upload_response.text

    list_response = client.get(f"/api/v1/claims/{real_claim}/documents", headers=auth_headers)

    assert list_response.status_code == 200, list_response.text
    documents = list_response.json()
    assert len(documents) == 1
    assert documents[0]["id"] == upload_response.json()[0]["id"]
    assert documents[0]["document_role"] == "OWN_VEHICLE"


def test_opening_form_fuses_real_extracted_data_from_two_documents(auth_headers, real_claim):
    own_payload = _build_synthetic_pdf(marque="TOYOTA", plate="AB-123-CD")
    adverse_payload = _build_synthetic_pdf(marque="RENAULT", plate="XY-999-ZZ")

    own_response = client.post(
        f"/api/v1/claims/{real_claim}/documents",
        files={"file": ("own.pdf", own_payload, "application/pdf")},
        data={"document_role": "OWN_VEHICLE"},
        headers=auth_headers,
    )
    assert own_response.status_code == 201, own_response.text

    adverse_response = client.post(
        f"/api/v1/claims/{real_claim}/documents",
        files={"file": ("adverse.pdf", adverse_payload, "application/pdf")},
        data={"document_role": "ADVERSE_VEHICLE"},
        headers=auth_headers,
    )
    assert adverse_response.status_code == 201, adverse_response.text

    form_response = client.get(
        f"/api/v1/claims/{real_claim}/documents/opening-form", headers=auth_headers
    )
    assert form_response.status_code == 200, form_response.text
    form = form_response.json()

    # Plate values come back hyphen-stripped: Normalizer.normalize_license_plate
    # canonicalizes "AB-123-CD" -> "AB123CD".
    assert form["numero_immatriculation"]["status"] == "FOUND"
    assert form["numero_immatriculation"]["value"] == "AB123CD"
    assert form["partie_adverse"]["immatriculation"]["status"] == "FOUND"
    assert form["partie_adverse"]["immatriculation"]["value"] == "XY999ZZ"
    assert form["partie_adverse"]["marque_vehicule"]["value"] == "RENAULT"


def test_ingest_document_rejects_unknown_claim(auth_headers):
    payload = _build_synthetic_pdf()
    fake_claim_id = str(uuid.uuid4())

    response = client.post(
        f"/api/v1/claims/{fake_claim_id}/documents",
        files={"file": ("constat.pdf", payload, "application/pdf")},
        headers=auth_headers,
    )

    assert response.status_code == 404


def test_opening_form_rejects_unknown_claim(auth_headers):
    fake_claim_id = str(uuid.uuid4())

    response = client.get(
        f"/api/v1/claims/{fake_claim_id}/documents/opening-form", headers=auth_headers
    )

    assert response.status_code == 404


def test_ingest_document_requires_auth(real_claim):
    payload = _build_synthetic_pdf()

    response = client.post(
        f"/api/v1/claims/{real_claim}/documents",
        files={"file": ("constat.pdf", payload, "application/pdf")},
    )

    assert response.status_code == 401


def test_ingesting_a_document_persists_a_real_validation_decision(auth_headers, real_claim):
    """
    Regression test: the pipeline already computes an EvidenceGraphResult
    per document, but before this it was discarded — GET .../validation
    always returned "No validation performed yet." for claims created
    through this endpoint. Confirms it's now real.
    """
    payload = _build_synthetic_pdf()

    upload_response = client.post(
        f"/api/v1/claims/{real_claim}/documents",
        files={"file": ("constat.pdf", payload, "application/pdf")},
        data={"document_role": "OWN_VEHICLE"},
        headers=auth_headers,
    )
    assert upload_response.status_code == 201, upload_response.text
    assert upload_response.json()[0]["pipeline_warnings"] == []

    validation_response = client.get(f"/api/v1/claims/{real_claim}/validation", headers=auth_headers)

    assert validation_response.status_code == 200, validation_response.text
    report = validation_response.json()
    assert report["claim_id"] == real_claim
    assert report["decision"] is not None
    assert "message" not in report  # that key only appears in the "never ran" placeholder


def test_correct_opening_form_field_persists_and_overrides_extraction(auth_headers, real_claim):
    payload = _build_synthetic_pdf(plate="AB-123-CD")

    upload_response = client.post(
        f"/api/v1/claims/{real_claim}/documents",
        files={"file": ("constat.pdf", payload, "application/pdf")},
        data={"document_role": "OWN_VEHICLE"},
        headers=auth_headers,
    )
    assert upload_response.status_code == 201, upload_response.text

    before = client.get(
        f"/api/v1/claims/{real_claim}/documents/opening-form", headers=auth_headers
    ).json()
    assert before["numero_police"]["status"] == "NOT_FOUND"

    patch_response = client.patch(
        f"/api/v1/claims/{real_claim}/documents/opening-form",
        json={"field_path": "numero_police", "value": "AXA-999888"},
        headers=auth_headers,
    )
    assert patch_response.status_code == 200, patch_response.text
    patched = patch_response.json()
    assert patched["numero_police"]["value"] == "AXA-999888"
    assert patched["numero_police"]["status"] == "FOUND"
    assert patched["numero_police"]["confidence"] == 1.0
    assert patched["numero_police"]["source"]["extraction_method"] == "manual_correction"

    # Correction persists across a fresh fetch, not just the PATCH response.
    after = client.get(
        f"/api/v1/claims/{real_claim}/documents/opening-form", headers=auth_headers
    ).json()
    assert after["numero_police"]["value"] == "AXA-999888"

    # A correction also overrides an auto-extracted, otherwise-FOUND field.
    plate_patch = client.patch(
        f"/api/v1/claims/{real_claim}/documents/opening-form",
        json={"field_path": "numero_immatriculation", "value": "CORRECTED-PLATE"},
        headers=auth_headers,
    )
    assert plate_patch.status_code == 200, plate_patch.text
    assert plate_patch.json()["numero_immatriculation"]["value"] == "CORRECTED-PLATE"


def test_correct_opening_form_field_rejects_unknown_path(auth_headers, real_claim):
    response = client.patch(
        f"/api/v1/claims/{real_claim}/documents/opening-form",
        json={"field_path": "not_a_real_field", "value": "x"},
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_correct_opening_form_field_rejects_unknown_claim(auth_headers):
    fake_claim_id = str(uuid.uuid4())

    response = client.patch(
        f"/api/v1/claims/{fake_claim_id}/documents/opening-form",
        json={"field_path": "numero_police", "value": "x"},
        headers=auth_headers,
    )

    assert response.status_code == 404
