from alembic import op
import sqlalchemy as sa

def chainqueue_upgrade(major, minor, patch):
    r0_0_1_u()


def chainqueue_downgrade(major, minor, patch):
    r0_0_1_d()


def r0_0_1_u():
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

    op.create_table(
            'otx_state_log',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('otx_id', sa.Integer, sa.ForeignKey('otx.id'), nullable=False),
            sa.Column('date', sa.DateTime, nullable=False),
            sa.Column('status', sa.Integer, nullable=False),
            )

    op.create_table(
            'tx_cache',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('otx_id', sa.Integer, sa.ForeignKey('otx.id'), nullable=True),
            sa.Column('date_created', sa.DateTime, nullable=False),
            sa.Column('date_updated', sa.DateTime, nullable=False),
            sa.Column('date_checked', sa.DateTime, nullable=False),
            sa.Column('source_token_address', sa.String(42), nullable=False),
            sa.Column('destination_token_address', sa.String(42), nullable=False),
            sa.Column('sender', sa.String(42), nullable=False),
            sa.Column('recipient', sa.String(42), nullable=False),
            sa.Column('from_value', sa.NUMERIC(), nullable=False),
            sa.Column('to_value', sa.NUMERIC(), nullable=True),
            sa.Column('tx_index', sa.Integer, nullable=True),
            )


def r0_0_1_d():
    op.drop_table('tx_cache')
    op.drop_table('otx_state_log')
    op.drop_index('idx_otx_tx')
    op.drop_table('otx')
