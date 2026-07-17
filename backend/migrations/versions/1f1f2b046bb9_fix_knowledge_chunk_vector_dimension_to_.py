"""fix knowledge_chunk vector dimension to match real embedding model

Revision ID: 1f1f2b046bb9
Revises: c7c0f34e8cfd
Create Date: 2026-07-13 13:03:34.997001

"""
from typing import Sequence, Union

from alembic import op
import pgvector.sqlalchemy


# revision identifiers, used by Alembic.
revision: str = '1f1f2b046bb9'
down_revision: Union[str, Sequence[str], None] = 'c7c0f34e8cfd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    The knowledge_chunk.vector_embedding column was created as VECTOR(384) to
    match the dimensionality of the (now-removed) mock embedding provider.
    The platform's real embedding model, Ollama's mxbai-embed-large, produces
    1024-dimensional vectors. Any rows written under the old dimension were
    from the mock provider and are not real embeddings, so they are discarded
    rather than migrated.
    """
    op.execute("UPDATE knowledge_chunk SET vector_embedding = NULL")
    op.alter_column(
        'knowledge_chunk', 'vector_embedding',
        existing_type=pgvector.sqlalchemy.vector.VECTOR(dim=384),
        type_=pgvector.sqlalchemy.vector.VECTOR(dim=1024),
        existing_nullable=True,
        postgresql_using='NULL',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("UPDATE knowledge_chunk SET vector_embedding = NULL")
    op.alter_column(
        'knowledge_chunk', 'vector_embedding',
        existing_type=pgvector.sqlalchemy.vector.VECTOR(dim=1024),
        type_=pgvector.sqlalchemy.vector.VECTOR(dim=384),
        existing_nullable=True,
        postgresql_using='NULL',
    )
