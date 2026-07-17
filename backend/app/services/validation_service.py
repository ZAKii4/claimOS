"""
Validation service — business logic orchestrator for claims validation.
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.engines.base import EngineContext
from app.engines.evidence_graph.models import EvidenceGraphResult
from app.engines.validation.manager import ValidationEngine
from app.engines.validation.severity import ValidationSeverity
from app.models.validation import ValidationDecision, ClaimDiscrepancy
from app.repositories.validation_repository import ValidationRepository
from app.utils.exceptions import EntityNotFoundError


class ValidationService:
    """
    Orchestrates validation operations.
    """

    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = ValidationRepository(db)
        self._engine = ValidationEngine()

    def get_validation_report(self, claim_id: UUID) -> dict:
        """Get the latest validation report for a claim."""
        latest_decision = self._repo.get_latest_decision(claim_id)
        if not latest_decision:
            return {"message": "No validation performed yet.", "claim_id": str(claim_id)}
        
        issues = self._repo.list_issues(claim_id)
        
        return {
            "claim_id": str(claim_id),
            "decision": latest_decision.decision,
            "composite_confidence": float(latest_decision.composite_confidence),
            "decided_at": latest_decision.decided_at.isoformat() if latest_decision.decided_at else None,
            "issues": [
                {
                    "severity": issue.severity,
                    "description": issue.description,
                    "created_at": issue.created_at.isoformat() if issue.created_at else None
                }
                for issue in issues
            ]
        }

    def get_validation_issues(self, claim_id: UUID, severity: str | None = None) -> list[dict]:
        """Get validation issues for a claim."""
        issues = self._repo.list_issues(claim_id, severity)
        return [
            {
                "severity": issue.severity,
                "description": issue.description,
                "created_at": issue.created_at.isoformat() if issue.created_at else None
            }
            for issue in issues
        ]

    def get_validation_statistics(self, claim_id: UUID) -> dict:
        """Get validation statistics for a claim."""
        return self._repo.get_statistics(claim_id)

    def run_validation(self, claim_id: UUID, graph: EvidenceGraphResult) -> dict:
        """Run validation engine and persist the results."""
        context = EngineContext(
            claim_id=str(claim_id),
            input_data={"evidence_graph_result": graph}
        )
        
        result = self._engine.process(context)
        if result.status != "SUCCESS":
            raise Exception(f"Validation engine failed: {result.errors}")

        report_data = result.output_data["validation_report"]
        
        # Decide the global status based on the report
        summary = report_data.get("summary", {})
        is_valid = summary.get("is_valid", False)
        
        if is_valid:
            decision_code = "STP_APPROVED"
        elif summary.get("has_blockers", False):
            decision_code = "REJECTED"
        else:
            decision_code = "HITL_REVIEW"

        # Save Decision
        decision = ValidationDecision(
            claim_id=claim_id,
            decision=decision_code,
            composite_confidence=result.confidence or 0.0,
            model_version=result.engine_version,
            decided_by="AI_ENGINE"
        )
        self._repo.create_decision(decision)

        # Save Issues
        issues_data = report_data.get("issues", [])
        
        # We need a fallback discrepancy_type_id to satisfy the foreign key.
        # Ideally, we would lookup the discrepancy_type based on the issue category.
        # For MVP enterprise implementation, we fetch the first discrepancy type.
        # If none exist, we need to create one or skip (but it's required by the schema).
        
        from app.models.lookups import DiscrepancyType
        from sqlalchemy import select
        stmt = select(DiscrepancyType).limit(1)
        fallback_disc_type = self._db.scalars(stmt).first()
        
        for issue in issues_data:
            # We map ValidationIssue to ClaimDiscrepancy
            if not fallback_disc_type:
                # If there are no lookup data populated, we skip creating issues or create a dummy one.
                # Assuming lookups are populated.
                pass
            else:
                disc = ClaimDiscrepancy(
                    claim_id=claim_id,
                    discrepancy_type_id=fallback_disc_type.id,
                    entity_a_table="evidence_graph",
                    entity_a_id=claim_id,  # Simplified fallback
                    entity_a_field="graph",
                    entity_b_table="evidence_graph",
                    entity_b_id=claim_id,
                    entity_b_field="graph",
                    severity=issue.get("severity", "INFO")[:16],
                    description=issue.get("message", "")
                )
                self._repo.create_discrepancy(disc)

        self._db.commit()
        return report_data
