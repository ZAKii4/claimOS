from typing import Dict, Any, List
from pydantic import BaseModel
from app.local_ai.ollama.registry import LocalModelRegistry


class ResourceMetrics(BaseModel):
    cpu_usage_percent: float
    ram_usage_gb: float
    gpu_usage_percent: float
    vram_usage_gb: float
    active_models: int


class AIResourceManager:
    """Monitors and manages local hardware resources for AI models."""

    # Simulated metrics
    _simulated_cpu = 45.0
    _simulated_ram = 16.0
    _simulated_gpu = 60.0
    _simulated_vram = 12.0

    @classmethod
    def get_resource_status(cls) -> ResourceMetrics:
        """Returns the current hardware usage."""
        active_models = len([m for m in LocalModelRegistry.list_models() if m.is_loaded])
        return ResourceMetrics(
            cpu_usage_percent=cls._simulated_cpu + (active_models * 5.0),
            ram_usage_gb=cls._simulated_ram + (active_models * 2.0),
            gpu_usage_percent=cls._simulated_gpu + (active_models * 10.0),
            vram_usage_gb=cls._simulated_vram + (active_models * 4.0),
            active_models=active_models
        )

    @classmethod
    def optimize_resources(cls) -> Dict[str, Any]:
        """Unloads inactive models to free up VRAM if threshold is exceeded."""
        metrics = cls.get_resource_status()
        actions_taken = []
        
        # If VRAM > 20GB, force unload some models
        if metrics.vram_usage_gb > 20.0:
            for model in LocalModelRegistry.list_models():
                if model.is_loaded and model.name != "llama-3.1": # Keep base model
                    LocalModelRegistry.update_status(model.name, False)
                    actions_taken.append(f"Unloaded {model.name}")
                    
        return {
            "status": "OPTIMIZED",
            "vram_freed": len(actions_taken) * 4.0,
            "actions": actions_taken
        }
