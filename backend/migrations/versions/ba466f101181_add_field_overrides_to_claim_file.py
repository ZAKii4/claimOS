"""add field_overrides to claim_file

Revision ID: ba466f101181
Revises: 742264c03879
Create Date: 2026-07-14 15:47:47.119772

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ba466f101181'
down_revision: Union[str, Sequence[str], None] = '742264c03879'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'claim_file',
        sa.Column('field_overrides', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('claim_file', 'field_overrides')
