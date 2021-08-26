"""Otx state history

Revision ID: 3e43847c0717
Revises: 2215c497248b
Create Date: 2021-04-02 10:10:58.656139

"""
# revision identifiers, used by Alembic.
revision = '3e43847c0717'
down_revision = '2215c497248b'
branch_labels = None
depends_on = None

from chainqueue.db.migrations.default.versions.src.otx_state_history import upgrade, downgrade
