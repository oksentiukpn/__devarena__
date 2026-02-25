"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade():
    """Executes the database schema changes required to move forward to this revision"""
    ${upgrades if upgrades else "pass"}


def downgrade():
    """Reverts the changes made by the upgrade, returning the database to its previous state"""
    ${downgrades if downgrades else "pass"}
