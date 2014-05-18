"""Remove hstore Catalog.meta column

Revision ID: 7bd609ce275
Revises: 595ab4e89b02
Create Date: 2014-05-18 14:49:34.496641

"""

# revision identifiers, used by Alembic.
revision = '7bd609ce275'
down_revision = '595ab4e89b02'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy.ext.mutable import MutableDict


def upgrade():
    op.drop_column('catalog', 'meta')


def downgrade():
    meta = sa.Column('meta', MutableDict.as_mutable(HSTORE),
                     nullable=False,
                     default={},
                     index=True)
    op.add_column('catalog', meta)
