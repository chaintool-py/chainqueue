# external imports
from chainlib.error import DefaultErrorParser

# local imports
from chainqueue.encode import TxHexNormalizer


class Backend:
    """Base constructor for backend implementation.

    :param tx_normalizer: Transaction data normalizer
    :type tx_normalizer: Object implementing chainqueue.encode.TxHexNormalizer interface
    :param error_parser: Error parser to use for RPC calls within the backend component
    :type error_parser: Object implementing chainlib.error.DefaultErrorParser
    :param debug: Activate backend debugging
    :type debug: bool
    """
    def __init__(self, tx_normalizer=None, error_parser=None, debug=False):
        if error_parser == None:
            error_parser = DefaultErrorParser()
        self.error_parser = error_parser
        if tx_normalizer == None:
            tx_normalizer = TxHexNormalizer()
        self.tx_normalizer = tx_normalizer
        self.debug = debug


    def create(self, chain_spec, nonce, holder_address, tx_hash, signed_tx, obsolete_predecessors=True, session=None):
        """Create a new transaction record in backend.

        The nonce field is provided as a convenience to avoid needless resources spent on decoding the transaction data to retrieve it.

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
        raise NotImplementedError()


    def cache(self, tx, session=None):
        """Create a new cache record for existing outgoing transaction in backend.

        :param tx: Transaction dict representation
        :type tx: dict
        :param session: Sqlalchemy database session
        :type session: sqlalchemy.orm.Session
        :rtype: int
        :returns: 0 if successful
        """
        raise NotImplementedError()


    def get_otx(self, chain_spec, tx_hash, session=None):
        """Retrieve a single otx summary dictionary by transaction hash.

        :param chain_spec: Chain spec context to look up transaction with
        :type chain_spec: chainlib.chain.ChainSpec
        :param tx_hash: Transaction hash
        :type tx_hash: str
        :param session: Sqlalchemy database session
        :type session: sqlalchemy.orm.Session
        :rtype: dict
        :returns: otx record summary
        """
        raise NotImplementedError()


    def get(self, chain_spec, decoder, session=None, requeue=False, *args, **kwargs):
        """Gets transaction lists based on given criteria.

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
        raise NotImplementedError()


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
        raise NotImplementedError()


    def create_session(self, session=None):
        """Create or pass on a new backend connection session.

        :param session: Use existing session
        :type session: varies
        """
        raise NotImplementedError()


    def release_session(self, session):
        """Release resources held by session.

        :param session: Session to release
        :type session: varies
        """
        raise NotImplementedError()
