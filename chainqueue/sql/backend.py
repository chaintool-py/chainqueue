# standard imports
import logging
import urllib.error
import copy

# external imports
from sqlalchemy.exc import (
    IntegrityError,
    )
from chainlib.error import (
        RPCException,
        RPCNonceException,
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
        set_rejected,
        )
from chainqueue.sql.tx import cache_tx_dict
from chainqueue.backend import Backend

logg = logging.getLogger(__name__)


class SQLBackend(Backend):
    """SQL flavor of the chainqueue backend implementation.

    :param conn_spec: Backend-dependent connection specification string. See chainqueue.db.models.base.SessionBase.connect
    :type conn_spec: str
    :param tx_normalizer: Transaction data normalizer
    :type tx_normalizer: Object implementing chainqueue.encode.TxHexNormalizer interface
    :param error_parser: Error parser to use for RPC calls within the backend component
    :type error_parser: Object implementing chainlib.error.DefaultErrorParser
    :param pool_size: Connection pool size for pool-capable sql engines. See chainqueue.db.models.base.SessionBase.connect
    :type pool_size: int
    :param debug: Activate SQL engine level debug. See chainqueue.db.models.base.SessionBase.connect
    :type debug: bool
    """
    def __init__(self, conn_spec, tx_normalizer=None, error_parser=None, pool_size=0, debug=False, *args, **kwargs):
        super(SQLBackend, self).__init__(tx_normalizer=tx_normalizer, error_parser=error_parser, debug=debug) 
        SessionBase.connect(conn_spec, pool_size=pool_size, debug=debug)


    def create(self, chain_spec, nonce, holder_address, tx_hash, signed_tx, obsolete_predecessors=True, session=None):
        """Create a new transaction record in backend.

        The nonce field is provided as a convenience to avoid needless resources spent on decoding the transaction data to retrieve it. However, this means that no check will be performed to verify that nonce matches the nonce encoded in the transaction, and thus it is the caller's responsibility to ensure that it is correct.

        :param chain_spec: Chain spec to add record for
        :type chain_spec: chainlib.chain.ChainSpec
        :param nonce: Transaction nonce
        :type nonce: int
        :param holder_address: Address of transaction sender
        :type holder_address: str
        :param tx_hash: Transaction hash
        :type tx_hash: str
        :param signed_tx: Signed transaction data
        :type signed_tx: str
        :param obsolete_predecessors: If set, will mark older transactions with same nonce from holder_address as obsolete
        :type obsolete_predecessors: bool
        :param session: Sqlalchemy database session
        :type session: sqlalchemy.orm.Session
        :rtype: int
        :returns: 0 if successfully added
        """
        tx_hash = self.tx_normalizer.tx_hash(tx_hash)
        signed_tx = self.tx_normalizer.tx_wire(signed_tx)
        try:
            queue_create(chain_spec, nonce, holder_address, tx_hash, signed_tx, obsolete_predecessors=True, session=session)
        except IntegrityError as e:
            logg.warning('skipped possible duplicate insert {}'.format(e))
            return 1
        set_ready(chain_spec, tx_hash, session=session)
        return 0


    def cache(self, tx, session=None):
        """Create a new cache record for existing outgoing transaction in backend.

        :param tx: Transaction dict representation
        :type tx: dict
        :param session: Sqlalchemy database session
        :type session: sqlalchemy.orm.Session
        :rtype: int
        :returns: 0 if successful
        """
        ntx = copy.copy(tx)
        ntx['hash'] = self.tx_normalizer.tx_hash(ntx['hash'])
        ntx['from'] = self.tx_normalizer.wallet_address(ntx['from'])
        ntx['to'] = self.tx_normalizer.wallet_address(ntx['to'])
        ntx['source_token'] = self.tx_normalizer.executable_address(ntx['source_token'])
        ntx['destination_token'] = self.tx_normalizer.executable_address(ntx['destination_token'])

        (tx_dict, txc_id) = cache_tx_dict(ntx, session=session)
        logg.debug('cached {} db insert id {}'.format(tx_dict, txc_id))
        return 0


    def get_otx(self, chain_spec, tx_hash, session=None):
        """Retrieve a single otx summary dictionary by transaction hash.

        Alias of chainqueue.sql.query.get_tx

        :param chain_spec: Chain spec context to look up transaction with
        :type chain_spec: chainlib.chain.ChainSpec
        :param tx_hash: Transaction hash
        :type tx_hash: str
        :param session: Sqlalchemy database session
        :type session: sqlalchemy.orm.Session
        :rtype: dict
        :returns: otx record summary
        """
        tx_hash = self.tx_normalizer.tx_hash(tx_hash)
        return backend_get_tx(chain_spec, tx_hash, session=session)


    def get(self, chain_spec, decoder, session=None, requeue=False, *args, **kwargs):
        """Gets transaction lists based on given criteria.

        Calls chainqueue.sql.query.get_upcoming_tx. If requeue is True, the QUEUED status bit will be set on all matched transactions.

        :param chain_spec: Chain spec context to look up transactions for
        :type chain_spec: chainlib.chain.ChainSpec
        :param decoder: Decoder instance to parse values from serialized transaction data in record
        :type decoder: Function taking serialized tx as parameter
        :param session: Sqlalchemy database session
        :type session: sqlalchemy.orm.Session
        :param status: Only match transaction that have the given bits set
        :type status: int
        :param not_status: Only match transactions that have none of the given bits set
        :type not_status: int
        :param recipient: Only match transactions that has the given address as recipient
        :type recipient: str
        :param before: Only match tranaactions that were last checked before the given time
        :type before: datetime.datetime
        :param limit: Return at most given number of transaction. If 0, will return all matched transactions.
        :type limit: int
        :rtype: dict
        :returns: key value pairs of transaction hash and signed transaction data for all matching transactions
        """
        txs = get_upcoming_tx(chain_spec, status=kwargs.get('status'), decoder=decoder, not_status=kwargs.get('not_status', 0), recipient=kwargs.get('recipient'), before=kwargs.get('before'), limit=kwargs.get('limit', 0))
        if requeue:
            for tx_hash in txs.keys():
                set_ready(chain_spec, tx_hash, session=session)
        return txs

    
    def dispatch(self, chain_spec, rpc, tx_hash, payload, session=None):
        """Send a single queued transaction.

        :param chain_spec: Chain spec context for network send
        :type chain_spec: chainlib.chain.ChainSpec
        :param rpc: RPC connection to use for send
        :type rpc: chainlib.connection.RPCConnection
        :param tx_hash: Transaction hash of transaction to send
        :type tx_hash: str
        :param payload: Prepared RPC query to send
        :type payload: any
        :param session: Sqlalchemy database session
        :type session: sqlalchemy.orm.Session
        :rtype: int
        :returns: 0 if no error
        """
        tx_hash = self.tx_normalizer.tx_hash(tx_hash)
        set_reserved(chain_spec, tx_hash, session=session)
        fail = False
        r = 1
        try:
            rpc.do(payload, error_parser=self.error_parser)
            r = 0
        except ConnectionError as e:
            logg.error('dispatch {} connection error {}'.format(tx_hash, e))
            fail = True
        except urllib.error.URLError as e:
            logg.error('dispatch {} urllib error {}'.format(tx_hash, e))
            fail = True
        except RPCNonceException as e:
            logg.error('nonce error {} default {}'.format(tx_hash, e))
            set_rejected(chain_spec, tx_hash, session=session)
            return 1
        except RPCException as e:
            logg.exception('error! {}'.format(e))
            set_fubar(chain_spec, tx_hash, session=session)
            raise e

        set_sent(chain_spec, tx_hash, fail=fail, session=session)

        return r


    def create_session(self, session=None):
        """Alias for chainqueue.db.models.base.SessionBase.bind_session
        """
        return SessionBase.bind_session(session=session)


    def release_session(self, session):
        """Alias for chainqueue.db.models.base.SessionBase.release_session
        """
        return SessionBase.release_session(session=session)
