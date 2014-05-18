"""Add Catalog.metajson column

Revision ID: 595ab4e89b02
Revises: 40dd1894002b
Create Date: 2014-05-18 14:17:23.399896

"""

# revision identifiers, used by Alembic.
revision = '595ab4e89b02'
down_revision = '40dd1894002b'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, HSTORE
from sqlalchemy.ext.mutable import MutableDict


def upgrade():
    metajson = sa.Column('metajson', MutableDict.as_mutable(JSON),
                         default={})
    op.add_column('catalog', metajson)


def downgrade():
    op.drop_column('catalog', 'metajson')
    meta = sa.Column('meta', MutableDict.as_mutable(HSTORE),
                     nullable=False,
                     default={},
                     index=True)
    op.add_column('catalog', meta)
