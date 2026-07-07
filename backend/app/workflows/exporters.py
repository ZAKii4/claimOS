from app.workflows.models import WorkflowDefinition


class MermaidExporter:
    """Exports a WorkflowDefinition to a MermaidJS Graph."""
    
    @staticmethod
    def export(definition: WorkflowDefinition) -> str:
        lines = ["graph TD"]
        
        # Define nodes with appropriate shapes
        for node in definition.nodes:
            if node.type == "ExclusiveGateway":
                lines.append(f'    {node.id}{{"{node.name}"}}')
            elif node.type == "ParallelGateway":
                lines.append(f'    {node.id}(("{node.name}"))')
            else:
                lines.append(f'    {node.id}["{node.name}"]')
            
        # Define edges
        for edge in definition.edges:
            label = f"|{edge.condition_expression}|" if edge.condition_expression else ""
            lines.append(f'    {edge.source_id} -->{label} {edge.target_id}')
            
        return "\n".join(lines)
