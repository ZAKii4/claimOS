from typing import Dict
from collections import defaultdict


class MetricsEngine:
    """In-memory metrics aggregator."""
    
    counters: Dict[str, int] = defaultdict(int)
    histograms: Dict[str, list] = defaultdict(list)
    
    @classmethod
    def increment(cls, name: str, value: int = 1):
        cls.counters[name] += value
        
    @classmethod
    def record_latency(cls, name: str, duration_ms: float):
        cls.histograms[name].append(duration_ms)
        
    @classmethod
    def get_summary(cls) -> dict:
        summary = {"counters": dict(cls.counters), "latencies": {}}
        for name, values in cls.histograms.items():
            if values:
                summary["latencies"][name] = {
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values)
                }
        return summary

from prometheus_client import Counter, Histogram, Gauge, generate_latest
from typing import Any

class MetricsManager:
    """
    Manages Prometheus metrics for the platform.
    """
    def __init__(self):
        # API Metrics
        self.api_requests = Counter(
            'claimos_api_requests_total',
            'Total API Requests',
            ['method', 'endpoint', 'status']
        )
        self.api_latency = Histogram(
            'claimos_api_latency_seconds',
            'API Latency',
            ['endpoint']
        )
        
        # AI/LLM Metrics
        self.llm_latency = Histogram(
            'claimos_llm_inference_seconds',
            'LLM Inference Time',
            ['model']
        )
        self.llm_tokens = Counter(
            'claimos_llm_tokens_total',
            'Total Tokens Processed',
            ['model', 'type'] # type: prompt or completion
        )
        self.hallucination_score = Gauge(
            'claimos_ai_hallucination_score',
            'Estimated Hallucination Score (0-100)',
            ['model']
        )
        
        # Infrastructure Metrics
        self.gpu_vram_usage = Gauge(
            'claimos_gpu_vram_gb',
            'GPU VRAM Usage',
            ['gpu_id']
        )

    def get_metrics_payload(self) -> bytes:
        return generate_latest()

metrics_manager = MetricsManager()

