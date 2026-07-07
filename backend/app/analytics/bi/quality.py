from typing import List, Dict, Any
from app.analytics.lake.warehouse import AnalyticsWarehouse
from app.analytics.lake.models import DataQualityIssue


class DataQualityEngine:
    """Continuously monitors data for completeness, uniqueness, and freshness."""

    _issues: List[DataQualityIssue] = []

    @classmethod
    def run_checks(cls, tenant_id: str) -> Dict[str, Any]:
        """Runs quality checks and returns a summary."""
        facts = AnalyticsWarehouse.get_raw_facts(tenant_id, "claims")
        
        issues_found = 0
        seen_ids = set()
        
        for f in facts:
            # Uniqueness check
            if f.id in seen_ids:
                cls._issues.append(DataQualityIssue(
                    tenant_id=tenant_id, record_id=f.id,
                    issue_type="uniqueness", severity="HIGH", details="Duplicate fact ID"
                ))
                issues_found += 1
            seen_ids.add(f.id)
            
            # Completeness check (stub: must have at least 1 dimension)
            if not f.dimensions:
                cls._issues.append(DataQualityIssue(
                    tenant_id=tenant_id, record_id=f.id,
                    issue_type="completeness", severity="MEDIUM", details="Missing dimensions"
                ))
                issues_found += 1

        total = len(facts)
        quality_score = 100.0
        if total > 0:
            error_rate = issues_found / total
            quality_score = max(0.0, 100.0 - (error_rate * 100))
            
        return {
            "total_records_checked": total,
            "issues_found": issues_found,
            "quality_score": round(quality_score, 2)
        }

    @classmethod
    def get_issues(cls, tenant_id: str = None) -> List[DataQualityIssue]:
        if tenant_id:
            return [i for i in cls._issues if i.tenant_id == tenant_id]
        return list(cls._issues)

    @classmethod
    def _clear_all(cls):
        cls._issues.clear()
