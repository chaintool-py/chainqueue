# standard imports
import logging

# local imports
from chainqueue.db.models.base import SessionBase
from chainqueue.db import dsn_from_config

logg = logging.getLogger(__name__)


def setup_backend(config, debug=False):
        dsn = dsn_from_config(config)
        logg.debug('dsn {}'.format(dsn))
        SessionBase.connect(dsn, debug=debug)
