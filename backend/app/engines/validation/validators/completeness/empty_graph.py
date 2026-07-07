from app.engines.validation.base_rule import ValidationRule
from app.engines.validation.context import ValidationContext
from app.engines.validation.report import ValidationIssue
from app.engines.validation.severity import ValidationSeverity


class EmptyGraphRule(ValidationRule):
    """
    Checks if the evidence graph is completely empty.
    """

    @property
    def id(self) -> str:
        return "COMP-001"

    @property
    def name(self) -> str:
        return "Empty Evidence Graph"

    @property
    def category(self) -> str:
        return "COMPLETENESS"

    @property
    def description(self) -> str:
        return "Ensures that the claim contains at least some extracted entities."

    @property
    def severity(self) -> ValidationSeverity:
        return ValidationSeverity.BLOCKER

    def validate(self, context: ValidationContext) -> list[ValidationIssue]:
        issues = []
        if len(context.evidence_graph.nodes) == 0:
            issues.append(
                self.create_issue(
                    message="The claim has no extracted evidence nodes.",
                    explanation="No valid data could be extracted from the documents associated with this claim.",
                    suggested_correction="Verify the uploaded documents or run the OCR/Extraction pipeline again."
                )
            )
        return issues
