# standard imports
import logging
import urllib.error

# external imports
from sqlalchemy.exc import (
    IntegrityError,
    )
from chainlib.error import JSONRPCException
from hexathon import (
        add_0x,
        strip_0x,
        uniform as hex_uniform,
        )

# local imports
from chainqueue.sql.tx import create as queue_create
from chainqueue.db.models.base import SessionBase
from chainqueue.db.models.tx import TxCache
from chainqueue.sql.query import (
        get_upcoming_tx,
        get_tx as backend_get_tx,
        )
from chainqueue.sql.state import (
        set_ready,
        set_reserved,
        set_sent,
        set_fubar,
        )
from chainqueue.sql.tx import cache_tx_dict

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
        (tx, txc_id) = cache_tx_dict(tx, session=session)
        logg.debug('cached {} db insert id {}'.format(tx, txc_id))
        return 0


    def get_tx(self, chain_spec, tx_hash, session=None):
        return backend_get_tx(chain_spec, tx_hash, session=session)


    def get(self, chain_spec, decoder, session=None, requeue=False, *args, **kwargs):
        txs = get_upcoming_tx(chain_spec, status=kwargs.get('status'), decoder=decoder, not_status=kwargs.get('not_status', 0), recipient=kwargs.get('recipient'), before=kwargs.get('before'), limit=kwargs.get('limit', 0))
        if requeue:
            for tx_hash in txs.keys():
                set_ready(chain_spec, tx_hash, session=session)
        return txs

    
    def dispatch(self, chain_spec, rpc, tx_hash, payload, session=None):
        set_reserved(chain_spec, tx_hash, session=session)
        fail = False
        r = 1
        try:
            rpc.do(payload)
            r = 0
        except ConnectionError as e:
            logg.error('dispatch {} connection error {}'.format(tx_hash, e))
            fail = True
        except urllib.error.URLError as e:
            logg.error('dispatch {} urllib error {}'.format(tx_hash, e))
            fail = True
        except JSONRPCException as e:
            logg.exception('error! {}'.format(e))
            set_fubar(chain_spec, tx_hash, session=session)
            raise e

        set_sent(chain_spec, tx_hash, fail=fail, session=session)

        return r


    def create_session(self, session=None):
        return SessionBase.bind_session(session=session)


    def release_session(self, session):
        return SessionBase.release_session(session=session)
