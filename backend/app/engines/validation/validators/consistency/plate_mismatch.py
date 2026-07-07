from app.engines.validation.base_rule import ValidationRule
from app.engines.validation.context import ValidationContext
from app.engines.validation.report import ValidationIssue
from app.engines.validation.severity import ValidationSeverity
from app.engines.evidence_graph.models import NodeType


class PlateMismatchRule(ValidationRule):
    """
    Flags an issue if multiple distinct vehicles have the exact same license plate.
    Note: Phase 9 Graph Merger resolves identical plates into a single MASTER node. 
    This rule might flag if the merger failed or if they were deliberately kept apart.
    For demonstration, we check for vehicles sharing plates without a MASTER node.
    """

    @property
    def id(self) -> str:
        return "CONS-001"

    @property
    def name(self) -> str:
        return "Duplicate License Plates"

    @property
    def category(self) -> str:
        return "CONSISTENCY"

    @property
    def description(self) -> str:
        return "Detects multiple vehicle entities sharing the same license plate."

    @property
    def severity(self) -> ValidationSeverity:
        return ValidationSeverity.CRITICAL

    def validate(self, context: ValidationContext) -> list[ValidationIssue]:
        issues = []
        vehicles = [n for n in context.evidence_graph.nodes if n.node_type == NodeType.VEHICLE]
        
        plates_map = {}
        for v in vehicles:
            # If it's a MASTER node, we ignore it for this duplicate check 
            # because the merger correctly handled it.
            if v.id.startswith("MASTER-"):
                continue
                
            entities = v.attributes.get("entities", [])
            plate = next((e.get("normalized_value") for e in entities if e.get("field_name") == "vehicle_plate"), None)
            
            if plate:
                if plate in plates_map:
                    issues.append(
                        self.create_issue(
                            message=f"License plate '{plate}' found on multiple distinct vehicles.",
                            explanation=f"Vehicle {v.id} and Vehicle {plates_map[plate].id} share the same plate.",
                            target_node_id=v.id,
                            suggested_correction="Verify if the extraction engine merged them correctly."
                        )
                    )
                else:
                    plates_map[plate] = v
                    
        return issues
