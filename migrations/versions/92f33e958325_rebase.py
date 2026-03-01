"""rebase

Revision ID: 92f33e958325
Revises: 73b594f75a10
Create Date: 2026-02-24 09:24:29.536730

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "92f33e958325"
down_revision = "73b594f75a10"
branch_labels = None
depends_on = None


def upgrade():
    # The 'points' column is already added by migration d07e5cc5295a (add points).
    # This migration previously duplicated that operation, causing a
    # DuplicateColumn error.  Nothing else to do here.
    pass


def downgrade():
    # Nothing to reverse since upgrade is now a no-op.
    pass
