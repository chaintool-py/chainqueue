class ChainQueueException(Exception):
    pass


class NotLocalTxError(ChainQueueException):
    """Exception raised when trying to access a tx not originated from a local task
    """
    pass


class TxStateChangeError(ChainQueueException):
    """Raised when an invalid state change of a queued transaction occurs
    """
    pass
