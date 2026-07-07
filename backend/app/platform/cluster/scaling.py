from typing import List
from app.platform.tenant.models import WorkerNode, ScalingRecommendation
from app.platform.cluster.nodes import NodeManager


class AutoScalingEngine:
    """Monitors cluster metrics and recommends scaling actions."""

    CPU_THRESHOLD_HIGH = 80.0
    CPU_THRESHOLD_LOW = 20.0
    QUEUE_THRESHOLD = 50

    @classmethod
    def evaluate(cls, queue_length: int = 0) -> ScalingRecommendation:
        active = NodeManager.get_active_nodes()
        count = len(active)

        if count == 0:
            return ScalingRecommendation(
                action="scale_out", reason="No active workers",
                current_workers=0, recommended_workers=1,
            )

        avg_cpu = sum(n.cpu_usage for n in active) / count
        avg_tasks = sum(n.task_count for n in active) / count

        if avg_cpu > cls.CPU_THRESHOLD_HIGH or queue_length > cls.QUEUE_THRESHOLD:
            return ScalingRecommendation(
                action="scale_out",
                reason=f"High load: CPU={avg_cpu:.1f}%, queue={queue_length}",
                current_workers=count,
                recommended_workers=count + 1,
            )

        if avg_cpu < cls.CPU_THRESHOLD_LOW and count > 1 and queue_length == 0:
            return ScalingRecommendation(
                action="scale_in",
                reason=f"Low load: CPU={avg_cpu:.1f}%",
                current_workers=count,
                recommended_workers=count - 1,
            )

        return ScalingRecommendation(
            action="no_change",
            reason=f"Stable: CPU={avg_cpu:.1f}%, queue={queue_length}",
            current_workers=count,
            recommended_workers=count,
        )
