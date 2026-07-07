from typing import Dict, List, Optional
from app.workflows.models import WorkflowDefinition, WorkflowInstance


class WorkflowRepository:
    """In-memory persistence for Workflows."""
    
    definitions: Dict[str, WorkflowDefinition] = {}
    instances: Dict[str, WorkflowInstance] = {}
    
    @classmethod
    def save_definition(cls, definition: WorkflowDefinition):
        cls.definitions[definition.id] = definition
        
    @classmethod
    def get_definition(cls, def_id: str) -> Optional[WorkflowDefinition]:
        return cls.definitions.get(def_id)
        
    @classmethod
    def get_all_definitions(cls) -> List[WorkflowDefinition]:
        return list(cls.definitions.values())
        
    @classmethod
    def save_instance(cls, instance: WorkflowInstance):
        cls.instances[instance.id] = instance
        
    @classmethod
    def get_instance(cls, instance_id: str) -> Optional[WorkflowInstance]:
        return cls.instances.get(instance_id)
        
    @classmethod
    def get_all_instances(cls) -> List[WorkflowInstance]:
        return list(cls.instances.values())
