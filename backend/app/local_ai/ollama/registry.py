from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class LocalModelMeta(BaseModel):
    name: str
    version: str
    parameters_size: str  # e.g., "8B", "32B"
    memory_required_mb: int
    context_window: int
    avg_throughput_tps: float
    supported_languages: List[str]
    expertise: List[str]
    quality_level: str  # "HIGH", "MEDIUM", "FAST"
    is_loaded: bool = False


class LocalModelRegistry:
    """Central registry of all available local models."""

    _models: Dict[str, LocalModelMeta] = {
        "llama-3.1": LocalModelMeta(
            name="llama-3.1", version="v3.1", parameters_size="8B", memory_required_mb=4096,
            context_window=128000, avg_throughput_tps=45.0, supported_languages=["en", "fr"],
            expertise=["General Conversation", "Instruction Following"], quality_level="MEDIUM"
        ),
        "qwen-2.5": LocalModelMeta(
            name="qwen-2.5", version="v2.5", parameters_size="14B", memory_required_mb=8192,
            context_window=32000, avg_throughput_tps=35.0, supported_languages=["en", "fr", "zh"],
            expertise=["Complex Reasoning", "Entity Extraction"], quality_level="HIGH"
        ),
        "deepseek-r1": LocalModelMeta(
            name="deepseek-r1", version="v1.0", parameters_size="33B", memory_required_mb=16384,
            context_window=16000, avg_throughput_tps=20.0, supported_languages=["en", "fr"],
            expertise=["Analysis", "Reflection", "Fraud Detection"], quality_level="HIGH"
        ),
        "mistral": LocalModelMeta(
            name="mistral", version="v0.2", parameters_size="7B", memory_required_mb=4096,
            context_window=8000, avg_throughput_tps=50.0, supported_languages=["en", "fr"],
            expertise=["Summarization", "Report Generation"], quality_level="FAST"
        ),
        "gemma-3": LocalModelMeta(
            name="gemma-3", version="v3", parameters_size="9B", memory_required_mb=6144,
            context_window=8000, avg_throughput_tps=40.0, supported_languages=["en"],
            expertise=["Classification"], quality_level="MEDIUM"
        ),
        "granite": LocalModelMeta(
            name="granite", version="v1", parameters_size="13B", memory_required_mb=8192,
            context_window=8000, avg_throughput_tps=30.0, supported_languages=["en", "fr"],
            expertise=["Legal Analysis"], quality_level="HIGH"
        ),
        "phi-4": LocalModelMeta(
            name="phi-4", version="v4", parameters_size="3B", memory_required_mb=2048,
            context_window=4000, avg_throughput_tps=80.0, supported_languages=["en"],
            expertise=["OCR Cleaning", "Data Formatting"], quality_level="FAST"
        ),
        "nomic-embed": LocalModelMeta(
            name="nomic-embed", version="v1.5", parameters_size="137M", memory_required_mb=1024,
            context_window=8192, avg_throughput_tps=500.0, supported_languages=["en", "fr"],
            expertise=["Embeddings"], quality_level="HIGH"
        ),
        "bge-m3": LocalModelMeta(
            name="bge-m3", version="v1", parameters_size="567M", memory_required_mb=2048,
            context_window=8192, avg_throughput_tps=300.0, supported_languages=["multi"],
            expertise=["Multilingual Embeddings"], quality_level="HIGH"
        )
    }

    @classmethod
    def list_models(cls) -> List[LocalModelMeta]:
        return list(cls._models.values())

    @classmethod
    def get_model(cls, name: str) -> Optional[LocalModelMeta]:
        return cls._models.get(name)

    @classmethod
    def update_status(cls, name: str, is_loaded: bool):
        if name in cls._models:
            cls._models[name].is_loaded = is_loaded

    @classmethod
    def _reset(cls):
        for m in cls._models.values():
            m.is_loaded = False
