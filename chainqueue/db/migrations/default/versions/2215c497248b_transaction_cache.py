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

from chainqueue.db.migrations.default.versions.src.tx_cache import upgrade, downgrade
