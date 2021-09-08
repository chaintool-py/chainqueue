# standard imports
import datetime

# local imports
from chainqueue.enum import StatusBits


class Adapter:
    """Base class defining interface to be implemented by chainqueue adapters.

    The chainqueue adapter collects the following actions:

    - add: add a transaction to the queue
    - upcoming: get queued transactions ready to be sent to network
    - dispatch: send a queued transaction to the network
    - translate: decode details of a transaction
    - create_session, release_session: session management to control queue state integrity

    :param backend: Chainqueue backend
    :type backend: TODO - abstract backend class. Must implement get, create_session, release_session
    :param pending_retry_threshold: seconds delay before retrying a transaction stalled in the newtork
    :type pending_retry_threshold: int
    :param error_retry_threshold: seconds delay before retrying a transaction that incurred a recoverable error state
    :type error_retry_threshold: int
    """

    def __init__(self, backend, pending_retry_threshold=0, error_retry_threshold=0):
        self.backend = backend
        self.pending_retry_threshold = datetime.timedelta(pending_retry_threshold)
        self.error_retry_threshold = datetime.timedelta(error_retry_threshold)


    def add(self, bytecode, chain_spec, session=None):
        """Add a transaction to the queue.

        :param bytecode: Transaction wire format bytecode, in hex
        :type bytecode: str
        :param chain_spec: Chain spec to use for transaction decode
        :type chain_spec: chainlib.chain.ChainSpec
        :param session: Backend state integrity session
        :type session: varies
        """
        raise NotImplementedError()


    def translate(self, bytecode, chain_spec):
        """Decode details of a transaction.

        :param bytecode: Transaction wire format bytecode, in hex
        :type bytecode: str
        :param chain_spec: Chain spec to use for transaction decode
        :type chain_spec: chainlib.chain.ChainSpec
        """
        raise NotImplementedError()


    def get(self, tx_hash, chain_spec, session=None):
        """Retrieve serialized transaction represented by the given transaction hash.

        :param chain_spec: Chain spec to use for transaction decode
        :type chain_spec: chainlib.chain.ChainSpec
        :param tx_hash: Transaction hash, in hex
        :type tx_hash: str
        :param session: Backend state integrity session
        :type session: varies
        """
        raise NotImplementedError()


    def dispatch(self, chain_spec, rpc, tx_hash, signed_tx, session=None):
        """Send a queued transaction to the network.

        :param chain_spec: Chain spec to use to identify the transaction network
        :type chain_spec: chainlib.chain.ChainSpec
        :param rpc: RPC connection to use for transaction send
        :type rpc: chainlib.connection.RPCConnection
        :param tx_hash: Transaction hash (checksum of transaction), in hex
        :type tx_hash: str
        :param signed_tx: Transaction wire format bytecode, in hex
        :type signed_tx: str
        :param session: Backend state integrity session
        :type session: varies
        """
        raise NotImplementedError()


    def upcoming(self, chain_spec, session=None):
        """Get queued transactions ready to be sent to the network.

        The transactions will be a combination of newly submitted transactions, previously sent but stalled transactions, and transactions that could temporarily not be submitted.

        :param chain_spec: Chain spec to use to identify the transaction network
        :type chain_spec: chainlib.chain.ChainSpec
        :param session: Backend state integrity session
        :type session: varies
        """
        raise NotImplementedError()


    def create_session(self, session=None):
        """Create a session context to guarantee atomic state change in backend.

        :param session: If specified, session will be used instead of creating a new one
        :type session: varies
        """
        return self.backend.create_session(session)


    def release_session(self, session=None):
        """Release a session context created by create_session.

        If session parameter is defined, final session destruction will be deferred to the initial provider of the session. In other words; if create_session was called with a session, release_session should symmetrically be called with the same session.

        :param session: Session context.
        :type session: varies
        """
        return self.backend.release_session(session)
