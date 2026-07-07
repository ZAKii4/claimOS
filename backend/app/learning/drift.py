import math
from typing import Dict, List, Tuple
from app.learning.models import DriftReport


class DriftEngine:
    @staticmethod
    def _kl_divergence(p: List[float], q: List[float]) -> float:
        """Calculate the Kullback-Leibler divergence D(P || Q) in pure Python."""
        epsilon = 1e-9
        return sum(p[i] * math.log((p[i] + epsilon) / (q[i] + epsilon)) for i in range(len(p)))

    @staticmethod
    def _jensen_shannon_divergence(p: List[float], q: List[float]) -> float:
        """Calculate the Jensen-Shannon divergence."""
        m = [0.5 * (p[i] + q[i]) for i in range(len(p))]
        return 0.5 * DriftEngine._kl_divergence(p, m) + 0.5 * DriftEngine._kl_divergence(q, m)

    @staticmethod
    def _population_stability_index(expected: List[float], actual: List[float]) -> float:
        """Calculate Population Stability Index (PSI)."""
        epsilon = 1e-4
        psi = 0.0
        for e, a in zip(expected, actual):
            e_val = max(e, epsilon)
            a_val = max(a, epsilon)
            psi += (a_val - e_val) * math.log(a_val / e_val)
        return psi

    @staticmethod
    def _align_distributions(dist_a: Dict[str, int], dist_b: Dict[str, int]) -> Tuple[List[float], List[float]]:
        """Align two dictionary distributions into lists of probabilities."""
        all_keys = set(dist_a.keys()).union(set(dist_b.keys()))
        
        total_a = sum(dist_a.values()) or 1
        total_b = sum(dist_b.values()) or 1
        
        p = []
        q = []
        
        for k in sorted(list(all_keys)):
            p.append(dist_a.get(k, 0) / total_a)
            q.append(dist_b.get(k, 0) / total_b)
            
        return p, q

    def detect_drift(self, dataset_a_id: str, dist_a: Dict[str, int], dataset_b_id: str, dist_b: Dict[str, int]) -> DriftReport:
        p, q = self._align_distributions(dist_a, dist_b)
        
        if not p or not q:
            return DriftReport(
                dataset_a=dataset_a_id,
                dataset_b=dataset_b_id,
                kl_divergence=0.0,
                population_stability_index=0.0,
                drift_detected=False,
                drift_details={}
            )
            
        kl_div = self._kl_divergence(p, q)
        psi = self._population_stability_index(p, q)
        
        # Thresholds: PSI > 0.2 indicates significant shift. KL > 0.1 indicates shift.
        is_drifting = psi > 0.2 or kl_div > 0.1
        
        return DriftReport(
            dataset_a=dataset_a_id,
            dataset_b=dataset_b_id,
            kl_divergence=kl_div,
            population_stability_index=psi,
            drift_detected=is_drifting,
            drift_details={
                "jensen_shannon": self._jensen_shannon_divergence(p, q),
                "threshold_exceeded": "PSI" if psi > 0.2 else "KL" if kl_div > 0.1 else None
            }
        )
