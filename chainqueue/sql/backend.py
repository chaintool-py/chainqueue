# standard imports
import logging

# external imports
from sqlalchemy.exc import (
    IntegrityError,
    )

# local imports
from chainqueue.sql.tx import create as queue_create
from chainqueue.db.models.base import SessionBase

logg = logging.getLogger(__name__)


class SQLBackend:

    def __init__(self, conn_spec, *args, **kwargs):
        SessionBase.connect(conn_spec, pool_size=kwargs.get('poolsize', 0), debug=kwargs.get('debug', False))


    def create(self, chain_spec, nonce, holder_address, tx_hash, signed_tx, obsolete_predecessors=True, session=None):
        try:
            queue_create(chain_spec, nonce, holder_address, tx_hash, signed_tx, obsolete_predecessors=True, session=None)
        except IntegrityError as e:
            logg.warning('skipped possible duplicate insert {}'.format(e))
            return 1
        return 0


    def create_session(self):
        return SessionBase.create_session()
