from typing import List, Dict, Any, Optional
from app.analytics.lake.models import FactRecord


class AnalyticsWarehouse:
    """Manages fact tables and multidimensional queries."""

    _facts: List[FactRecord] = []

    @classmethod
    def insert_fact(cls, fact: FactRecord):
        cls._facts.append(fact)

    @classmethod
    def query_aggregate(
        cls, 
        tenant_id: str, 
        fact_type: str, 
        dimension_filters: Dict[str, str] = None
    ) -> Dict[str, float]:
        """Simple aggregation (sum) for a specific fact type and dimension filters."""
        results = [f for f in cls._facts if f.tenant_id == tenant_id and f.fact_type == fact_type]
        
        if dimension_filters:
            for k, v in dimension_filters.items():
                results = [f for f in results if f.dimensions.get(k) == v]

        aggregated: Dict[str, float] = {}
        for f in results:
            for measure_name, measure_value in f.measures.items():
                aggregated[measure_name] = aggregated.get(measure_name, 0.0) + measure_value
                
        return aggregated

    @classmethod
    def get_raw_facts(cls, tenant_id: str, fact_type: str) -> List[FactRecord]:
        return [f for f in cls._facts if f.tenant_id == tenant_id and f.fact_type == fact_type]

    @classmethod
    def _clear_all(cls):
        """For testing only."""
        cls._facts.clear()
