class NotLocalTxError(Exception):
    """Exception raised when trying to access a tx not originated from a local task
    """
    pass
