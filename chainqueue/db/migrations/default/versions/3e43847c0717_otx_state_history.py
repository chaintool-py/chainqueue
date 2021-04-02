"""Otx state history

Revision ID: 3e43847c0717
Revises: 2215c497248b
Create Date: 2021-04-02 10:10:58.656139

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3e43847c0717'
down_revision = '2215c497248b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
            'otx_state_log',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('otx_id', sa.Integer, sa.ForeignKey('otx.id'), nullable=False),
            sa.Column('date', sa.DateTime, nullable=False),
            sa.Column('status', sa.Integer, nullable=False),
            )


def downgrade():
    op.drop_table('otx_state_log')
