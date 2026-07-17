"""add document role and extracted data to claim document

Revision ID: 5f6c6be935d7
Revises: cd68c40c6376
Create Date: 2026-07-14 11:41:01.445596

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5f6c6be935d7'
down_revision: Union[str, Sequence[str], None] = 'cd68c40c6376'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'claim_document',
        sa.Column('document_role', sa.String(length=32), nullable=True),
    )
    op.add_column(
        'claim_document',
        sa.Column('extracted_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('claim_document', 'extracted_data')
    op.drop_column('claim_document', 'document_role')
