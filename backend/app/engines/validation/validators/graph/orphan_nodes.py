from app.engines.validation.base_rule import ValidationRule
from app.engines.validation.context import ValidationContext
from app.engines.validation.report import ValidationIssue
from app.engines.validation.severity import ValidationSeverity
from app.engines.evidence_graph.models import NodeType


class OrphanNodeRule(ValidationRule):
    """
    Detects if nodes (like Policy or Vehicle) are completely isolated in the graph.
    """

    @property
    def id(self) -> str:
        return "GRPH-001"

    @property
    def name(self) -> str:
        return "Orphan Graph Nodes"

    @property
    def category(self) -> str:
        return "GRAPH"

    @property
    def description(self) -> str:
        return "Identifies important nodes that have no edges connecting them to the rest of the claim."

    @property
    def severity(self) -> ValidationSeverity:
        return ValidationSeverity.WARNING

    def validate(self, context: ValidationContext) -> list[ValidationIssue]:
        issues = []
        
        # Build an adjacency set
        connected_node_ids = set()
        for edge in context.evidence_graph.edges:
            connected_node_ids.add(edge.source_id)
            connected_node_ids.add(edge.target_id)
            
        for node in context.evidence_graph.nodes:
            if node.node_type in [NodeType.VEHICLE, NodeType.POLICY]:
                if node.id not in connected_node_ids:
                    issues.append(
                        self.create_issue(
                            message=f"Orphan {node.node_type.value} node detected.",
                            explanation=f"Node {node.id} has no relationships to the claim or other entities.",
                            target_node_id=node.id,
                            suggested_correction="Ensure the Reasoning engine successfully links nodes."
                        )
                    )
                    
        return issues
