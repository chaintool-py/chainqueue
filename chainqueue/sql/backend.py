# standard imports
import logging

# external imports
from sqlalchemy.exc import (
    IntegrityError,
    )
from chainlib.error import JSONRPCException

# local imports
from chainqueue.sql.tx import create as queue_create
from chainqueue.db.models.base import SessionBase
from chainqueue.db.models.tx import TxCache
from chainqueue.sql.query import get_upcoming_tx
from chainqueue.sql.state import (
        set_ready,
        set_reserved,
        set_sent,
        )

logg = logging.getLogger(__name__)


class SQLBackend:

    def __init__(self, conn_spec, *args, **kwargs):
        SessionBase.connect(conn_spec, pool_size=kwargs.get('poolsize', 0), debug=kwargs.get('debug', False))


    def create(self, chain_spec, nonce, holder_address, tx_hash, signed_tx, obsolete_predecessors=True, session=None):
        try:
            queue_create(chain_spec, nonce, holder_address, tx_hash, signed_tx, obsolete_predecessors=True, session=session)
        except IntegrityError as e:
            logg.warning('skipped possible duplicate insert {}'.format(e))
            return 1
        set_ready(chain_spec, tx_hash, session=session)
        return 0


    def cache(self, tx, session=None):
        txc = TxCache(tx['hash'], tx['from'], tx['to'], tx['source_token'], tx['destination_token'], tx['from_value'], tx['to_value'], session=session)
        session.add(txc)
        session.flush()
        logg.debug('cache {}'.format(txc))
        return 0


    def get(self, chain_spec, typ, decoder):
        txs = get_upcoming_tx(chain_spec, typ, decoder=decoder)
        return txs

    
    def dispatch(self, chain_spec, rpc, tx_hash, payload, session=None):
        set_reserved(chain_spec, tx_hash, session=session)
        fail = False
        r = 1
        try:
            rpc.do(payload)
            r = 0
        except ConnectionError:
            fail = True
        except JSONRPCException as e:
            logg.error('error! {}'.format(e))

        logg.debug('foo')
        set_sent(chain_spec, tx_hash, fail=fail, session=session)
        return r


    def create_session(self):
        return SessionBase.create_session()
