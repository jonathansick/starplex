"""Rename Catalog.metajson to meta

Revision ID: 496d441a7733
Revises: 7bd609ce275
Create Date: 2014-05-18 15:00:52.019316

"""

# revision identifiers, used by Alembic.
revision = '496d441a7733'
down_revision = '7bd609ce275'

from alembic import op


def upgrade():
    op.alter_column('catalog', 'metajson', new_column_name='meta')


def downgrade():
    op.alter_column('catalog', 'meta', new_column_name='metajson')
