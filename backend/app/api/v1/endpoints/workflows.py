import uuid
from fastapi import APIRouter, HTTPException
from app.workflows.repository import WorkflowRepository
from app.workflows.models import WorkflowInstance, WorkflowState
from app.workflows.executor import WorkflowExecutor

router = APIRouter(prefix="/workflows", tags=["Enterprise Workflow Engine"])


@router.get("/definitions")
def list_definitions():
    return [d.model_dump() for d in WorkflowRepository.get_all_definitions()]


@router.get("/definitions/{def_id}")
def get_definition(def_id: str):
    definition = WorkflowRepository.get_definition(def_id)
    if not definition:
        raise HTTPException(status_code=404, detail="Definition not found")
    return definition.model_dump()


@router.post("/instances")
async def start_instance(def_id: str, context_vars: dict = None):
    definition = WorkflowRepository.get_definition(def_id)
    if not definition:
        raise HTTPException(status_code=404, detail="Definition not found")
        
    instance = WorkflowInstance(
        id=str(uuid.uuid4()),
        definition_id=def_id
    )
    if context_vars:
        instance.context.variables = context_vars
        
    WorkflowRepository.save_instance(instance)
    
    # Fire and forget execution (in a real app, use Celery/BackgroundTasks)
    executor = WorkflowExecutor(definition, instance)
    await executor.run()
    
    return instance.model_dump()


@router.get("/instances/{instance_id}")
def get_instance(instance_id: str):
    instance = WorkflowRepository.get_instance(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    return instance.model_dump()


@router.post("/instances/{instance_id}/resume")
async def resume_instance(instance_id: str, task_id: str, updates: dict = None):
    instance = WorkflowRepository.get_instance(instance_id)
    if not instance or instance.state != WorkflowState.SUSPENDED:
        raise HTTPException(status_code=400, detail="Instance cannot be resumed")
        
    # Mark specific task as complete if needed, update context
    if updates:
        for k, v in updates.items():
            instance.context.set(k, v)
            
    definition = WorkflowRepository.get_definition(instance.definition_id)
    executor = WorkflowExecutor(definition, instance)
    await executor.run()
    
    return instance.model_dump()
