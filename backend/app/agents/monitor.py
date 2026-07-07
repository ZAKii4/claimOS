from typing import Dict, Any


class AgentMonitor:
    """
    Global monitor for agent performance across the platform.
    In MVP, just an in-memory aggregator.
    """
    def __init__(self):
        self.stats: Dict[str, Dict[str, Any]] = {}
        
    def record_execution(self, agent_id: str, success: bool, duration_ms: int):
        if agent_id not in self.stats:
            self.stats[agent_id] = {
                "total_calls": 0,
                "successes": 0,
                "failures": 0,
                "total_duration": 0
            }
            
        st = self.stats[agent_id]
        st["total_calls"] += 1
        st["total_duration"] += duration_ms
        if success:
            st["successes"] += 1
        else:
            st["failures"] += 1
            
    def get_metrics(self) -> Dict[str, Any]:
        metrics = {}
        for agent_id, st in self.stats.items():
            avg_latency = st["total_duration"] / st["total_calls"] if st["total_calls"] > 0 else 0
            success_rate = st["successes"] / st["total_calls"] if st["total_calls"] > 0 else 0
            metrics[agent_id] = {
                "total_calls": st["total_calls"],
                "success_rate": success_rate,
                "avg_latency_ms": avg_latency
            }
        return metrics
