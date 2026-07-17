import uuid

import pytest

from app.core.database import get_session_factory
from app.models.lookups import DocumentType
from app.repositories.document_repository import DocumentRepository


@pytest.fixture
def db_session():
    Session = get_session_factory()
    db = Session()
    try:
        yield db
    finally:
        db.close()


def test_get_or_create_document_type_creates_new_type(db_session):
    family = f"Test Family {uuid.uuid4().hex[:8]}"
    repo = DocumentRepository(db_session)

    created = repo.get_or_create_document_type(family)
    db_session.commit()

    assert created.label_fr == family
    assert created.label_ar == family
    assert created.code

    fetched = db_session.query(DocumentType).filter(DocumentType.id == created.id).first()
    assert fetched is not None
    fetched_id = fetched.id
    db_session.query(DocumentType).filter(DocumentType.id == created.id).delete()
    db_session.commit()
    assert fetched_id == created.id


def test_get_or_create_document_type_is_idempotent(db_session):
    family = f"Idempotent Family {uuid.uuid4().hex[:8]}"
    repo = DocumentRepository(db_session)

    first = repo.get_or_create_document_type(family)
    db_session.commit()
    second = repo.get_or_create_document_type(family)
    db_session.commit()

    assert first.id == second.id

    db_session.query(DocumentType).filter(DocumentType.id == first.id).delete()
    db_session.commit()
