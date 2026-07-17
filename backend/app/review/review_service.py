import logging

from sqlalchemy.orm import Session

from app.learning.manager import LearningManager
from app.review.review_repository import ReviewRepository
from app.review.review_schemas import CorrectionPayload
from app.review.websocket import review_manager

logger = logging.getLogger("claimOS.review")


class ReviewService:
    def __init__(self, db: Session):
        self.repo = ReviewRepository(db)
        self.learning_manager = LearningManager()

    def lock_claim(self, claim_id: str, operator_id: str) -> dict:
        success = self.repo.lock_session(claim_id, operator_id)
        if success:
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(review_manager.broadcast_lock(claim_id, operator_id))
            except RuntimeError:
                pass
            return {"status": "success", "message": f"Claim {claim_id} locked by {operator_id}"}
        return {"status": "error", "message": "Claim is already locked or does not exist."}

    def unlock_claim(self, claim_id: str, operator_id: str) -> dict:
        success = self.repo.unlock_session(claim_id, operator_id)
        if success:
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(review_manager.broadcast_unlock(claim_id))
            except RuntimeError:
                pass
            return {"status": "success", "message": f"Claim {claim_id} unlocked."}
        return {"status": "error", "message": "Could not unlock claim."}

    def apply_correction(self, claim_id: str, operator_id: str, payload: CorrectionPayload) -> dict:
        session = self.repo.get_session(claim_id)
        if not session or session.locked_by != operator_id:
            return {"status": "error", "message": "You must lock the claim before applying corrections."}

        # Log Audit Trail
        self.repo.log_audit(
            claim_id=claim_id,
            actor=operator_id,
            action=payload.action,
            reason=payload.reason,
            old_value=payload.old_value,
            new_value=payload.new_value
        )

        # In a real system, we'd also trigger a TrainingFeedback generation here
        return {"status": "success", "message": "Correction applied and audited."}

    def finalize_review(self, claim_id: str, operator_id: str, final_status: str, reason: str) -> dict:
        session = self.repo.get_session(claim_id)
        if not session or session.locked_by != operator_id:
            return {"status": "error", "message": "You must lock the claim before finalizing."}

        self.repo.log_audit(claim_id, operator_id, f"FINALIZED_{final_status}", reason)
        self.repo.complete_session(claim_id, "COMPLETED")
        self._collect_learning_feedback(session, claim_id)

        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(review_manager.broadcast_unlock(claim_id))
        except RuntimeError:
            pass

        return {"status": "success", "message": f"Claim {claim_id} finalized as {final_status}."}

    def _collect_learning_feedback(self, session, claim_id: str) -> None:
        """Ingest the finalized ReviewSession's audit trail into the Learning Platform."""
        audit_logs = [
            {
                "action": audit.action,
                "old_value": audit.old_value,
                "new_value": audit.new_value,
                "actor": audit.actor,
            }
            for audit in self.repo.get_audits(claim_id)
        ]
        if not audit_logs:
            return

        session_data = {"claim_id": session.claim_id, "id": session.id}
        try:
            samples = self.learning_manager.process_review_session(session_data, audit_logs)
            if samples:
                self.learning_manager.build_and_export_datasets(samples)
        except Exception:
            logger.exception("Failed to collect learning feedback for claim %s", claim_id)
