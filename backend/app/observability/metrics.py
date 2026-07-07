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
