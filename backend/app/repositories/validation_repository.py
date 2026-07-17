"""
Validation repository.

Handles data access for ValidationDecision, ValidationFieldFlag, and ClaimDiscrepancy.
"""

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.validation import ValidationDecision, ValidationFieldFlag, ClaimDiscrepancy
from app.repositories.base_repository import BaseRepository

class ValidationRepository(BaseRepository[ValidationDecision]):
    """Repository for ValidationDecision entities."""

    def __init__(self, db: Session) -> None:
        super().__init__(ValidationDecision, db)

    def get_latest_decision(self, claim_id: UUID) -> ValidationDecision | None:
        """Get the most recent validation decision for a claim."""
        stmt = (
            select(ValidationDecision)
            .where(ValidationDecision.claim_id == claim_id)
            .order_by(ValidationDecision.decided_at.desc())
        )
        return self._db.scalars(stmt).first()

    def list_issues(self, claim_id: UUID, severity: str | None = None) -> list[ClaimDiscrepancy]:
        """List discrepancies/issues for a claim, optionally filtered by severity."""
        stmt = select(ClaimDiscrepancy).where(ClaimDiscrepancy.claim_id == claim_id)
        if severity:
            stmt = stmt.where(ClaimDiscrepancy.severity == severity)
        stmt = stmt.order_by(ClaimDiscrepancy.created_at.desc())
        return list(self._db.scalars(stmt).all())

    def create_decision(self, decision: ValidationDecision) -> ValidationDecision:
        """Create a new validation decision."""
        return self.create(decision)

    def create_discrepancy(self, discrepancy: ClaimDiscrepancy) -> ClaimDiscrepancy:
        """Create a new discrepancy."""
        self._db.add(discrepancy)
        return discrepancy

    def get_statistics(self, claim_id: UUID) -> dict:
        """Get basic validation statistics from DB."""
        latest = self.get_latest_decision(claim_id)
        issues = self.list_issues(claim_id)
        
        return {
            "has_decision": latest is not None,
            "latest_decision": latest.decision if latest else None,
            "total_issues": len(issues),
            "critical_issues": sum(1 for i in issues if i.severity == "CRITICAL"),
            "warning_issues": sum(1 for i in issues if i.severity == "WARNING"),
            "info_issues": sum(1 for i in issues if i.severity == "INFO"),
            "composite_confidence": float(latest.composite_confidence) if latest else 0.0
        }
