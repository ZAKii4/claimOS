"""make ocr_hocr_uri nullable on document_page

Revision ID: 742264c03879
Revises: 5f6c6be935d7
Create Date: 2026-07-14 12:22:33.252651

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '742264c03879'
down_revision: Union[str, Sequence[str], None] = '5f6c6be935d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # No step in the document pipeline generates an hOCR file today (OCR
    # results are stored as structured JSON, not hOCR) — a NOT NULL
    # constraint here would just force a fake placeholder into every row.
    op.alter_column("document_page", "ocr_hocr_uri", nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("document_page", "ocr_hocr_uri", nullable=False)
