from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from app.local_ai.ollama.registry import LocalModelRegistry, LocalModelMeta
from app.local_ai.ollama.cluster import OllamaClusterManager
from app.local_ai.ollama.router import ModelRoutingEngine
from app.local_ai.infrastructure.resources import AIResourceManager
from app.local_ai.infrastructure.sandbox import LocalAISandbox
from app.local_ai.infrastructure.embeddings import EmbeddingManager

router = APIRouter(prefix="/local-ai", tags=["Local AI & Ollama Ecosystem"])


class ModelNameRequest(BaseModel):
    model_name: str


class SandboxRequest(BaseModel):
    model_name: str
    prompt: str


class EmbeddingsRequest(BaseModel):
    texts: List[str]
    model_name: str = "nomic-embed"


@router.get("/models", response_model=List[LocalModelMeta])
def list_models():
    """Lists all local Ollama models in the registry."""
    return LocalModelRegistry.list_models()


@router.post("/models/load")
def load_model(req: ModelNameRequest):
    """Loads a specific model into memory."""
    success = OllamaClusterManager.load_model(req.model_name)
    if not success:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"status": "Loaded", "model": req.model_name}


@router.post("/models/unload")
def unload_model(req: ModelNameRequest):
    """Unloads a specific model to free VRAM."""
    success = OllamaClusterManager.unload_model(req.model_name)
    if not success:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"status": "Unloaded", "model": req.model_name}


@router.get("/cluster")
def cluster_status():
    """Gets the Ollama cluster status."""
    return OllamaClusterManager.get_cluster_status()


@router.get("/resources")
def get_resources():
    """Gets hardware resources monitoring (CPU, RAM, GPU, VRAM)."""
    return AIResourceManager.get_resource_status()


@router.post("/resources/optimize")
def optimize_resources():
    """Optimizes resources by unloading inactive models if VRAM is saturated."""
    return AIResourceManager.optimize_resources()


@router.post("/sandbox/run")
def run_sandbox_experiment(req: SandboxRequest):
    """Runs a prompt against a local model in the isolated sandbox."""
    exp = LocalAISandbox.run_experiment(req.model_name, req.prompt)
    if exp.status.startswith("FAILED"):
        raise HTTPException(status_code=404, detail="Model not found for sandbox")
    return exp


@router.post("/embeddings")
def generate_embeddings(req: EmbeddingsRequest):
    """Generates local embeddings using the specified model."""
    try:
        embeddings = EmbeddingManager.generate_embeddings(req.texts, req.model_name)
        return {"embeddings_count": len(embeddings), "dimensions": len(embeddings[0]) if embeddings else 0}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/router/task/{task_type}")
def get_route_for_task(task_type: str):
    """Returns the optimal model for a specific task."""
    model = ModelRoutingEngine.route_task(task_type)
    return {"task": task_type, "optimal_model": model.name if model else None}
