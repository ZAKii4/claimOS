from typing import Any

from app.core.database import get_session_factory
from app.models.knowledge import TenantEmbedding


class VectorRepository:
    """
    Real, Postgres/pgvector-backed CRUD for tenant-scoped ad-hoc embeddings
    (e.g. hybrid RAG query context). Backed by the `tenant_embedding` table.
    """

    def __init__(self):
        self.SessionLocal = get_session_factory()

    async def add_embedding(
        self,
        tenant_id: str,
        document_id: str,
        chunk_index: int,
        text: str,
        embedding: list[float],
        metadata: dict[str, Any] = None,
    ):
        db = self.SessionLocal()
        try:
            row = TenantEmbedding(
                tenant_id=tenant_id,
                document_id=document_id,
                chunk_index=chunk_index,
                text=text,
                embedding=embedding,
                metadata_json=metadata or {},
            )
            db.add(row)
            db.commit()
            return True
        finally:
            db.close()

    async def search_similar(
        self, tenant_id: str, query_embedding: list[float], top_k: int = 5
    ) -> list[dict[str, Any]]:
        if not query_embedding:
            return []

        db = self.SessionLocal()
        try:
            rows = (
                db.query(
                    TenantEmbedding,
                    TenantEmbedding.embedding.cosine_distance(query_embedding).label("distance"),
                )
                .filter(TenantEmbedding.tenant_id == tenant_id)
                .order_by("distance")
                .limit(top_k)
                .all()
            )

            return [
                {
                    "score": 1.0 - (distance or 0.0),
                    "document_id": row.document_id,
                    "text": row.text,
                    "metadata": row.metadata_json,
                }
                for row, distance in rows
            ]
        finally:
            db.close()


vector_repo = VectorRepository()
