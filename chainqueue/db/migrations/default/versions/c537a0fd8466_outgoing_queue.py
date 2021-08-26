"""Outgoing queue

Revision ID: c537a0fd8466
Revises: 
Create Date: 2021-04-02 10:04:27.092819

"""
# revision identifiers, used by Alembic.
revision = 'c537a0fd8466'
down_revision = None
branch_labels = None
depends_on = None

from chainqueue.db.migrations.default.versions.src.otx import upgrade, downgrade
