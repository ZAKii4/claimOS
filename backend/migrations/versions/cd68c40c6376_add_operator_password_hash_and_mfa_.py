"""add operator password hash and mfa secret

Revision ID: cd68c40c6376
Revises: c2293ec9c602
Create Date: 2026-07-13 16:46:23.325422

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cd68c40c6376'
down_revision: Union[str, Sequence[str], None] = 'c2293ec9c602'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('operator', sa.Column('hashed_password', sa.String(length=256), nullable=True))
    op.add_column('operator', sa.Column('mfa_secret', sa.String(length=64), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('operator', 'mfa_secret')
    op.drop_column('operator', 'hashed_password')
