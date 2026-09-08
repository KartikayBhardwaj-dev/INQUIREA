"""Database updated

Revision ID: cb2fe0d6baed
Revises: 442dd66f6dcc
Create Date: 2026-09-02 08:45:14.569347

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "cb2fe0d6baed"
down_revision: Union[str, Sequence[str], None] = "442dd66f6dcc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    The database already contains all schema changes represented
    by this migration, so there is nothing to execute.
    """
    pass


def downgrade() -> None:
    """Downgrade schema.

    The schema objects represented by this migration already existed
    before Alembic revision tracking was synchronized, so they are
    intentionally left untouched.
    """
    pass