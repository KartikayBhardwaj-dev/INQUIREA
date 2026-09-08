"""Change email embedding dimension to 384

Revision ID: 0d4a4f836705
Revises: cb2fe0d6baed
Create Date: 2026-09-03
"""

from typing import Sequence, Union

from alembic import op


revision: str = "0d4a4f836705"
down_revision: Union[str, Sequence[str], None] = "cb2fe0d6baed"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Change email embedding dimension from 1536 to 384."""
    op.execute(
        """
        ALTER TABLE email_embeddings
        ALTER COLUMN embedding TYPE vector(384)
        """
    )


def downgrade() -> None:
    """Change email embedding dimension back to 1536."""
    op.execute(
        """
        ALTER TABLE email_embeddings
        ALTER COLUMN embedding TYPE vector(1536)
        """
    )