"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

import app

${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade():
    op.execute('SET foreign_key_checks = 0;')

    ${upgrades if upgrades else "pass"}

    op.execute('SET foreign_key_checks = 1;')


def downgrade():
    op.execute('SET foreign_key_checks = 0;')

    ${downgrades if downgrades else "pass"}

    op.execute('SET foreign_key_checks = 1;')