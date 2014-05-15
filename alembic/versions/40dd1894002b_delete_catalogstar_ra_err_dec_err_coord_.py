"""Delete CatalogStar ra_err,dec_err,coord columns

Revision ID: 40dd1894002b
Revises: None
Create Date: 2014-05-15 13:49:14.726270

"""

# revision identifiers, used by Alembic.
revision = '40dd1894002b'
down_revision = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.drop_column('catalog_star', 'dec_err')
    op.drop_column('catalog_star', 'ra_err')
    op.drop_column('catalog_star', 'coord')
    # op.drop_index('idx_catalog_star_coord', table_name='catalog_star')


def downgrade():
    # op.create_index('idx_catalog_star_coord', 'catalog_star', ['coord'], unique=False)
    op.add_column('catalog_star', sa.Column('coord', sa.Geography(geometry_type=u'POINT', srid=4326), autoincrement=False, nullable=True))
    op.add_column('catalog_star', sa.Column('ra_err', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True))
    op.add_column('catalog_star', sa.Column('dec_err', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True))
