from alembic import op
import sqlalchemy as sa

from chainqueue.db.migrations.default.versions.src.otx import (
        upgrade as upgrade_otx,
        downgrade as downgrade_otx,
        )
from chainqueue.db.migrations.default.versions.src.tx_cache import (
        upgrade as upgrade_tx_cache,
        downgrade as downgrade_tx_cache,
        )
from chainqueue.db.migrations.default.versions.src.otx_state_history import (
        upgrade as upgrade_otx_state_history,
        downgrade as downgrade_otx_state_history,
        )

def chainqueue_upgrade(major=0, minor=0, patch=1):
    r0_0_1_u()


def chainqueue_downgrade(major=0, minor=0, patch=1):
    r0_0_1_d()


def r0_0_1_u():
    upgrade_otx()
    upgrade_tx_cache()
    upgrade_otx_state_history()

def r0_0_1_d():
    downgrade_otx_state_history()
    downgrade_tx_cache()
    downgrade_otx()
