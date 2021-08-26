from alembic import op
import sqlalchemy as sa

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
