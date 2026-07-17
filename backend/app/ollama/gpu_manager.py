from typing import Dict, Any, List

class GPUManager:
    """
    Manages Model Eviction and VRAM Scheduling.
    (Simulated abstraction as we don't have direct nvidia-smi access).
    """
    def __init__(self):
        self.total_vram_gb = 16.0
        self.loaded_models: Dict[str, float] = {}
        
        # Static mock model sizes
        self.model_sizes = {
            "llama3.1:latest": 4.7,
            "qwen2.5:latest": 4.0,
            "mistral:latest": 4.1,
            "nomic-embed-text:latest": 0.5
        }

    def load_model(self, model_name: str) -> bool:
        """Loads a model into VRAM, evicting if necessary."""
        if model_name in self.loaded_models:
            return True
            
        size = self.model_sizes.get(model_name, 4.0)
        
        # Evict until we have space
        while self.get_used_vram() + size > self.total_vram_gb:
            if not self.loaded_models:
                raise ValueError("Model is too large for total VRAM")
            # Evict the oldest/first model
            model_to_evict = next(iter(self.loaded_models))
            del self.loaded_models[model_to_evict]
            
        self.loaded_models[model_name] = size
        return True

    def unload_model(self, model_name: str):
        if model_name in self.loaded_models:
            del self.loaded_models[model_name]

    def get_used_vram(self) -> float:
        return sum(self.loaded_models.values())
        
    def get_gpu_metrics(self) -> Dict[str, Any]:
        used = self.get_used_vram()
        return {
            "total_vram": self.total_vram_gb,
            "used_vram": used,
            "free_vram": self.total_vram_gb - used,
            "loaded_models": list(self.loaded_models.keys()),
            "utilization_percent": (used / self.total_vram_gb) * 100
        }

gpu_manager = GPUManager()
