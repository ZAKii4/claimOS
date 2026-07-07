import pytest
from app.review.database import Base, engine, SessionLocal
from app.review.review_schemas import ReviewSessionCreate, CorrectionPayload
from app.review.review_repository import ReviewRepository
from app.review.review_service import ReviewService
from datetime import datetime


@pytest.fixture(scope="module")
def setup_db():
    # Setup
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    # Teardown
    db.close()
    Base.metadata.drop_all(bind=engine)


def test_review_lifecycle(setup_db):
    db = setup_db
    repo = ReviewRepository(db)
    service = ReviewService(db)
    claim_id = "CLAIM-123"
    
    # 1. Create a session (e.g. from pipeline)
    session_data = ReviewSessionCreate(
        claim_id=claim_id,
        queue_name="QUEUE_HUMAN_REVIEW",
        priority=10,
        sla_deadline=datetime.utcnow(),
        evidence_graph={"nodes": [], "edges": []},
        validation_report={"issues": []},
        decision_reason="Validation score below threshold."
    )
    repo.create_session(session_data)
    
    # 2. Check Inbox
    inbox = repo.get_inbox()
    assert len(inbox) == 1
    assert inbox[0].claim_id == claim_id
    assert inbox[0].status == "PENDING"
    
    # 3. Operator locks the claim
    res = service.lock_claim(claim_id, operator_id="OP-01")
    assert res["status"] == "success"
    
    # Check it's locked
    session = repo.get_session(claim_id)
    assert session.locked_by == "OP-01"
    assert session.status == "IN_PROGRESS"
    
    # 4. Another operator tries to lock it
    res2 = service.lock_claim(claim_id, operator_id="OP-02")
    assert res2["status"] == "error"
    
    # 5. Operator applies a correction
    payload = CorrectionPayload(
        action="CORRECTED_BBOX",
        old_value={"x": 10},
        new_value={"x": 20},
        reason="OCR missed the edge"
    )
    res_correct = service.apply_correction(claim_id, "OP-01", payload)
    assert res_correct["status"] == "success"
    
    # Check Audit
    audits = session.audits
    assert len(audits) == 1
    assert audits[0].action == "CORRECTED_BBOX"
    
    # 6. Operator finalizes
    res_fin = service.finalize_review(claim_id, "OP-01", "COMPLETED", "Looks good now.")
    assert res_fin["status"] == "success"
    
    # Check it's no longer in inbox
    assert len(repo.get_inbox()) == 0
    final_session = repo.get_session(claim_id)
    assert final_session.status == "COMPLETED"
    assert final_session.locked_by is None
