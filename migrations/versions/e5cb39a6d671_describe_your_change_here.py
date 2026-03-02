"""describe_your_change_here

Revision ID: e5cb39a6d671
Revises: 70e2cdd8b96b
Create Date: 2026-02-23 11:00:11.725962

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e5cb39a6d671'
down_revision = '70e2cdd8b96b'
branch_labels = None
depends_on = None


def upgrade():
    """No-op migration: points column is added in 92f33e958325_rebase.py."""
    pass


def downgrade():
    """No-op downgrade matching the no-op upgrade."""
    pass
