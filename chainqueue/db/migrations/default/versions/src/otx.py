from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
            'otx',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('date_created', sa.DateTime, nullable=False),
            sa.Column('date_updated', sa.DateTime, nullable=False),
            sa.Column('nonce', sa.Integer, nullable=False),
            sa.Column('tx_hash', sa.Text, nullable=False),
            sa.Column('signed_tx', sa.Text, nullable=False),
            sa.Column('status', sa.Integer, nullable=False, default=0),
            sa.Column('block', sa.Integer),
            )
    op.create_index('idx_otx_tx', 'otx', ['tx_hash'], unique=True)


def downgrade():
    op.drop_index('idx_otx_tx')
    op.drop_table('otx')
