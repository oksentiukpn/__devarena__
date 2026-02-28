"""merge conflicting heads

Revision ID: 852cad9bb17c
Revises: 92f33e958325, e5cb39a6d671
Create Date: 2026-02-25 16:12:46.877005

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '852cad9bb17c'
down_revision = ('92f33e958325', 'e5cb39a6d671')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
