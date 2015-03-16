"""Add json to CatalogStar and Observation

Revision ID: effa43e7773
Revises: 55d5d0c4db29
Create Date: 2015-03-16 16:05:59.191553

"""

# revision identifiers, used by Alembic.
revision = 'effa43e7773'
down_revision = '55d5d0c4db29'

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.mutable import MutableDict


def upgrade():
    meta_catalogstar = sa.Column('meta', MutableDict.as_mutable(JSON),
                                 default={})
    op.add_column('catalog_star', meta_catalogstar)

    meta_obs = sa.Column('meta', MutableDict.as_mutable(JSON),
                         default={})
    op.add_column('observation', meta_obs)


def downgrade():
    op.drop_column('observation', 'meta')
    op.drop_column('catalog_star', 'meta')
