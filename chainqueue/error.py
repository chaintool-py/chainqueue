class ChainQueueException(Exception):
    """Base class for chainqueue related exceptions
    """
    pass


class NotLocalTxError(ChainQueueException):
    """Exception raised when trying to access a tx not originated from a local task
    """

    def __init__(self, tx_hash, block=None):
        super(NotLocalTxError, self).__init__(tx_hash, block)


class TxStateChangeError(ChainQueueException):
    """Raised when an invalid state change of a queued transaction occurs
    """
    pass


class CacheIntegrityError(ChainQueueException):
    """Raised when cached data does not match raw transaction data
    """
    pass


class BackendIntegrityError(ChainQueueException):
    """Raised when queue backend has invalid state
    """
    pass


class DuplicateTxError(ChainQueueException):
    """Backend already knows transaction
    """
    pass
