from app.engines.validation.base_rule import ValidationRule
from app.engines.validation.context import ValidationContext
from app.engines.validation.report import ValidationIssue
from app.engines.validation.severity import ValidationSeverity


class ExcessiveDuplicatesRule(ValidationRule):
    """
    Fraud heuristic: Checks if there are an unusually high number of merged duplicates 
    (e.g., the same license plate submitted 5 times in different parts of the claim).
    """

    @property
    def id(self) -> str:
        return "FRUD-001"

    @property
    def name(self) -> str:
        return "Excessive Merged Entities"

    @property
    def category(self) -> str:
        return "FRAUD_HEURISTIC"

    @property
    def description(self) -> str:
        return "Raises an alert if a single MASTER node contains too many merged provenances."

    @property
    def severity(self) -> ValidationSeverity:
        return ValidationSeverity.WARNING

    def validate(self, context: ValidationContext) -> list[ValidationIssue]:
        issues = []
        
        for node in context.evidence_graph.nodes:
            if node.id.startswith("MASTER-"):
                if len(node.provenances) > 3:
                    issues.append(
                        self.create_issue(
                            message=f"Suspiciously high number of duplicated entities merged.",
                            explanation=f"Node {node.id} was formed by merging {len(node.provenances)} identical entities. This might indicate document stuffing or reuse.",
                            target_node_id=node.id,
                            suggested_correction="Flag for human anti-fraud review."
                        )
                    )
                    
        return issues
