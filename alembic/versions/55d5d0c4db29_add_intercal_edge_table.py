"""Add intercal_edge table

Revision ID: 55d5d0c4db29
Revises: 496d441a7733
Create Date: 2014-05-19 14:08:59.612695

"""

# revision identifiers, used by Alembic.
revision = '55d5d0c4db29'
down_revision = '496d441a7733'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'intercal_edge',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('from_id', sa.Integer(), nullable=True),
        sa.Column('to_id', sa.Integer(), nullable=True),
        sa.Column('bandpass_id', sa.Integer(), nullable=True),
        sa.Column('delta', sa.Float(), nullable=True),
        sa.Column('delta_err', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ['bandpass_id'], ['bandpass.id'],
            name=op.f('fk_intercal_edge_bandpass_id_bandpass'),
            ondelete='CASCADE'),
        sa.ForeignKeyConstraint(
            ['from_id'], ['catalog.id'],
            name=op.f('fk_intercal_edge_from_id_catalog'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(
            ['to_id'], ['catalog.id'],
            name=op.f('fk_intercal_edge_to_id_catalog'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_intercal_edge'))
    )


def downgrade():
    op.drop_table('intercal_edge')
