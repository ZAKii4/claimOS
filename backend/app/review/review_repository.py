from datetime import datetime

from sqlalchemy.orm import Session

from app.review.review_models import ReviewAudit, ReviewSession
from app.review.review_schemas import ReviewSessionCreate


class ReviewRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_session(self, claim_id: str) -> ReviewSession | None:
        return self.db.query(ReviewSession).filter(ReviewSession.claim_id == claim_id).first()

    def get_inbox(self) -> list[ReviewSession]:
        return self.db.query(ReviewSession).filter(ReviewSession.status == "PENDING").order_by(ReviewSession.priority.desc()).all()

    def create_session(self, session_data: ReviewSessionCreate) -> ReviewSession:
        db_session = ReviewSession(**session_data.model_dump())
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        return db_session

    def lock_session(self, claim_id: str, operator_id: str) -> bool:
        session = self.get_session(claim_id)
        if not session:
            return False

        # Pessimistic lock logic
        if session.locked_by and session.locked_by != operator_id:
            return False # Locked by someone else

        session.locked_by = operator_id
        session.locked_at = datetime.utcnow()
        session.status = "IN_PROGRESS"

        self.db.commit()
        return True

    def unlock_session(self, claim_id: str, operator_id: str) -> bool:
        session = self.get_session(claim_id)
        if not session or session.locked_by != operator_id:
            return False

        session.locked_by = None
        session.locked_at = None
        session.status = "PENDING"

        self.db.commit()
        return True

    def log_audit(self, claim_id: str, actor: str, action: str, reason: str, old_value: dict = None, new_value: dict = None) -> None:
        session = self.get_session(claim_id)
        if not session:
            return

        audit = ReviewAudit(
            session_id=session.id,
            actor=actor,
            action=action,
            reason=reason,
            old_value=old_value,
            new_value=new_value
        )
        self.db.add(audit)
        self.db.commit()

    def get_audits(self, claim_id: str) -> list[ReviewAudit]:
        session = self.get_session(claim_id)
        if not session:
            return []
        return session.audits

    def complete_session(self, claim_id: str, final_status: str) -> None:
        session = self.get_session(claim_id)
        if session:
            session.status = final_status
            session.locked_by = None
            session.locked_at = None
            self.db.commit()
