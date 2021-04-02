"""Transaction cache

Revision ID: 2215c497248b
Revises: c537a0fd8466
Create Date: 2021-04-02 10:09:11.923949

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2215c497248b'
down_revision = 'c537a0fd8466'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
            'tx_cache',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('otx_id', sa.Integer, sa.ForeignKey('otx.id'), nullable=True),
            sa.Column('date_created', sa.DateTime, nullable=False),
            sa.Column('date_updated', sa.DateTime, nullable=False),
            sa.Column('source_token_address', sa.String(42), nullable=False),
            sa.Column('destination_token_address', sa.String(42), nullable=False),
            sa.Column('sender', sa.String(42), nullable=False),
            sa.Column('recipient', sa.String(42), nullable=False),
            sa.Column('from_value', sa.NUMERIC(), nullable=False),
            sa.Column('to_value', sa.NUMERIC(), nullable=True),
            sa.Column('block_number', sa.BIGINT(), nullable=True),
            sa.Column('tx_index', sa.Integer, nullable=True),
            )


def downgrade():
    op.drop_table('tx_cache')
