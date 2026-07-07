from collections import defaultdict
from typing import Dict


class CostEngine:
    """Consolidates financial metrics across all components."""
    
    _costs_by_claim: Dict[str, float] = defaultdict(float)
    _costs_by_category: Dict[str, float] = defaultdict(float)
    
    @classmethod
    def record_cost(cls, category: str, amount: float, claim_id: str = None):
        cls._costs_by_category[category] += amount
        if claim_id:
            cls._costs_by_claim[claim_id] += amount
            
    @classmethod
    def get_summary(cls) -> dict:
        return {
            "total_by_category": dict(cls._costs_by_category),
            "total_by_claim": dict(cls._costs_by_claim),
            "global_total": sum(cls._costs_by_category.values())
        }
