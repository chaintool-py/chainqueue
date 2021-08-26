# standard imports
import enum


@enum.unique
class StatusBits(enum.IntEnum):
    """Individual bit flags that are combined to define the state and legacy of a queued transaction

    """
    QUEUED = 0x01 # transaction should be sent to network
    RESERVED = 0x02 # transaction is currently being handled by a thread
    IN_NETWORK = 0x08 # transaction is in network
   
    DEFERRED = 0x10 # an attempt to send the transaction to network has failed
    GAS_ISSUES = 0x20 # transaction is pending sender account gas funding

    LOCAL_ERROR = 0x100 # errors that originate internally from the component
    NODE_ERROR = 0x200 # errors originating in the node (invalid RLP input...)
    NETWORK_ERROR = 0x400 # errors that originate from the network (REVERT)
    UNKNOWN_ERROR = 0x800 # unclassified errors (the should not occur)

    FINAL = 0x1000 # transaction processing has completed
    OBSOLETE = 0x2000 # transaction has been replaced by a different transaction with higher fee
    MANUAL = 0x8000 # transaction processing has been manually overridden


@enum.unique
class StatusEnum(enum.IntEnum):
    """Semantic states intended for human consumption
    """
    PENDING = 0

    SENDFAIL = StatusBits.DEFERRED | StatusBits.LOCAL_ERROR
    RETRY = StatusBits.QUEUED | StatusBits.DEFERRED 
    READYSEND = StatusBits.QUEUED
    RESERVED = StatusBits.RESERVED

    OBSOLETED = StatusBits.OBSOLETE | StatusBits.IN_NETWORK

    WAITFORGAS = StatusBits.GAS_ISSUES

    SENT = StatusBits.IN_NETWORK
    FUBAR = StatusBits.FINAL | StatusBits.UNKNOWN_ERROR
    CANCELLED = StatusBits.IN_NETWORK | StatusBits.FINAL | StatusBits.OBSOLETE
    OVERRIDDEN = StatusBits.FINAL | StatusBits.OBSOLETE | StatusBits.MANUAL

    REJECTED = StatusBits.NODE_ERROR | StatusBits.FINAL
    REVERTED = StatusBits.IN_NETWORK | StatusBits.FINAL | StatusBits.NETWORK_ERROR
    SUCCESS = StatusBits.IN_NETWORK | StatusBits.FINAL 


def status_str(v, bits_only=False):
    """Render a human-readable string describing the status

    If the bit field exactly matches a StatusEnum value, the StatusEnum label will be returned.

    If a StatusEnum cannot be matched, the string will be postfixed with "*", unless explicitly instructed to return bit field labels only.

    :param v: Status bit field
    :type v: number
    :param bits_only: Only render individual bit labels.
    :type bits_only: bool
    :returns: Status string
    :rtype: str
    """
    s = ''
    if not bits_only:
        try:
            s = StatusEnum(v).name
            return s
        except ValueError:
            pass

    if v == 0:
        return 'NONE'

    for i in range(16):
        b = (1 << i)
        if (b & 0xffff) & v:
            n = StatusBits(b).name
            if len(s) > 0:
                s += ','
            s += n
    if not bits_only:
        s += '*'
    return s


def status_bytes(status=0):
    """Serialize a status bit field integer value to bytes.
   
    if invoked without an argument, it will return the serialization of an empty state.

    :param status: Status bit field
    :type status: number
    :returns: Serialized value
    :rtype: bytes
    """
    return status.to_bytes(8, byteorder='big')


def all_errors():
    """Bit mask of all error states

    :returns: Error flags
    :rtype: number
    """
    return StatusBits.LOCAL_ERROR | StatusBits.NODE_ERROR | StatusBits.NETWORK_ERROR | StatusBits.UNKNOWN_ERROR

errors = all_errors()

def is_error_status(v):
    """Check if value is an error state

    :param v: Status bit field
    :type v: number
    :returns: True if error
    :rtype: bool
    """
    return bool(v & all_errors())


__ignore_manual_value = ~StatusBits.MANUAL
def ignore_manual(v):
    """Reset the MANUAL bit from the given status

    :param v: Status bit field
    :type v: number
    :returns: Input state with manual bit removed
    :rtype: number
    """
    return v & __ignore_manual_value


def is_nascent(v):
    """Check if state is the empty state

    :param v: Status bit field
    :type v: number
    :returns: True if empty
    :rtype: bool
    """
    return ignore_manual(v) == StatusEnum.PENDING


def dead():
    """Bit mask defining whether a transaction is still likely to be processed on the network.

    :returns: Bit mask
    :rtype: number
    """
    return StatusBits.FINAL | StatusBits.OBSOLETE


def is_alive(v):
    """Check if transaction is still likely to be processed on the network.

    The contingency of "likely" refers to the case a transaction has been obsoleted after sent to the network, but the network still confirms the obsoleted transaction. The return value of this method will not change as a result of this, BUT the state itself will (as the FINAL bit will be set).

    :param v: Status bit field
    :type v: number
    :returns: True if status is not yet finalized
    :rtype: bool
    """
    return bool(v & dead() == 0)
