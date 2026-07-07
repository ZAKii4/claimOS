from typing import List, Dict, Any, Optional
from app.analytics.lake.models import DataLayer, LakeRecord


class DataLakeManager:
    """Manages the Medallion architecture storage (logical simulation)."""

    _storage: Dict[DataLayer, List[LakeRecord]] = {
        DataLayer.BRONZE: [],
        DataLayer.SILVER: [],
        DataLayer.GOLD: []
    }

    @classmethod
    def ingest_raw(cls, tenant_id: str, source_type: str, data: Dict[str, Any]) -> LakeRecord:
        """Ingest raw data into Bronze layer."""
        record = LakeRecord(
            tenant_id=tenant_id,
            layer=DataLayer.BRONZE,
            source_type=source_type,
            data=data
        )
        cls._storage[DataLayer.BRONZE].append(record)
        return record

    @classmethod
    def promote_to_silver(cls, bronze_record: LakeRecord, cleaned_data: Dict[str, Any]) -> LakeRecord:
        """Promote raw data to cleaned Silver layer."""
        record = LakeRecord(
            tenant_id=bronze_record.tenant_id,
            layer=DataLayer.SILVER,
            source_type=bronze_record.source_type,
            data=cleaned_data
        )
        cls._storage[DataLayer.SILVER].append(record)
        return record

    @classmethod
    def promote_to_gold(cls, tenant_id: str, source_type: str, aggregated_data: Dict[str, Any]) -> LakeRecord:
        """Promote to Gold layer for business intelligence."""
        record = LakeRecord(
            tenant_id=tenant_id,
            layer=DataLayer.GOLD,
            source_type=source_type,
            data=aggregated_data
        )
        cls._storage[DataLayer.GOLD].append(record)
        return record

    @classmethod
    def query(
        cls, 
        layer: DataLayer, 
        tenant_id: Optional[str] = None, 
        source_type: Optional[str] = None
    ) -> List[LakeRecord]:
        """Query the data lake."""
        results = cls._storage[layer]
        if tenant_id:
            results = [r for r in results if r.tenant_id == tenant_id]
        if source_type:
            results = [r for r in results if r.source_type == source_type]
        return list(results)

    @classmethod
    def _clear_all(cls):
        """For testing only."""
        cls._storage = {
            DataLayer.BRONZE: [],
            DataLayer.SILVER: [],
            DataLayer.GOLD: []
        }
