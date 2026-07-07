from abc import ABC, abstractmethod
from typing import Optional

from app.engines.validation.context import ValidationContext
from app.engines.validation.severity import ValidationSeverity
from app.engines.validation.report import ValidationIssue


class ValidationRule(ABC):
    """
    Base contract for all Validation Rules.
    Follows Single Responsibility Principle: One rule = one check.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def category(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def severity(self) -> ValidationSeverity:
        pass

    @property
    def supported_claim_types(self) -> list[str]:
        """Return a list of claim families this rule applies to. Empty list means ALL."""
        return []

    def is_applicable(self, context: ValidationContext) -> bool:
        """Determines if the rule should run for the given context."""
        # By default, runs for all. Can be overridden.
        # Example: check if context.evidence_graph relates to supported_claim_types
        return True

    @abstractmethod
    def validate(self, context: ValidationContext) -> list[ValidationIssue]:
        """
        Executes the validation logic.
        Returns a list of ValidationIssues (empty list if no issues found).
        """
        pass
        
    def create_issue(
        self, 
        message: str, 
        explanation: str, 
        target_node_id: Optional[str] = None,
        target_edge_id: Optional[str] = None,
        suggested_correction: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> ValidationIssue:
        """Helper to create a standardized issue from this rule."""
        return ValidationIssue(
            rule_id=self.id,
            rule_name=self.name,
            category=self.category,
            severity=self.severity,
            message=message,
            explanation=explanation,
            target_node_id=target_node_id,
            target_edge_id=target_edge_id,
            suggested_correction=suggested_correction,
            metadata=metadata or {}
        )
