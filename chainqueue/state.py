# standard imports
import logging

# external imports
from hexathon import strip_0x

# local imports
from chainqueue.db.models.otx import Otx
from chainqueue.db.models.tx import TxCache
from chainqueue.db.models.base import SessionBase
from chainqueue.db.enum import (
        StatusEnum,
        StatusBits,
        is_nascent,
        )
from chainqueue.db.models.otx import OtxStateLog
from chainqueue.error import (
        NotLocalTxError,
        TxStateChangeError,
        )

logg = logging.getLogger().getChild(__name__)


def set_sent(tx_hash, fail=False):
    """Used to set the status after a send attempt

    :param tx_hash: Transaction hash of record to modify
    :type tx_hash: str, 0x-hex
    :param fail: if True, will set a SENDFAIL status, otherwise a SENT status. (Default: False)
    :type fail: boolean
    :raises NotLocalTxError: If transaction not found in queue.
    :returns: True if tx is known, False otherwise
    :rtype: boolean
    """
    session = SessionBase.create_session()
    o = Otx.load(tx_hash, session=session)
    if o == None:
        logg.warning('not local tx, skipping {}'.format(tx_hash))
        session.close()
        return False

    try:
        if fail:
            o.sendfail(session=session)
        else:
            o.sent(session=session)
    except TxStateChangeError as e:
        logg.exception('set sent fail: {}'.format(e))
        session.close()
        raise(e)
    except Exception as e:
        logg.exception('set sent UNEXPECED fail: {}'.format(e))
        session.close()
        raise(e)


    session.commit()
    session.close()

    return tx_hash


def set_final(tx_hash, block=None, fail=False):
    """Used to set the status of an incoming transaction result. 

    :param tx_hash: Transaction hash of record to modify
    :type tx_hash: str, 0x-hex
    :param block: Block number if final status represents a confirmation on the network
    :type block: number
    :param fail: if True, will set a SUCCESS status, otherwise a REVERTED status. (Default: False)
    :type fail: boolean
    :raises NotLocalTxError: If transaction not found in queue.
    """
    session = SessionBase.create_session()
    o = Otx.load(tx_hash, session=session)
    
    if o == None:
        session.close()
        raise NotLocalTxError('queue does not contain tx hash {}'.format(tx_hash))

    session.flush()

    try:
        if fail:
            o.minefail(block, session=session)
        else:
            o.success(block, session=session)
        session.commit()
    except TxStateChangeError as e:
        logg.exception('set final fail: {}'.format(e))
        session.close()
        raise(e)
    except Exception as e:
        logg.exception('set final UNEXPECTED fail: {}'.format(e))
        session.close()
        raise(e)

    q = session.query(TxCache)
    q = q.join(Otx)
    q = q.filter(Otx.tx_hash==strip_0x(tx_hash))
    o  = q.first()

    session.close()

    return tx_hash
    

def set_cancel(tx_hash, manual=False):
    """Used to set the status when a transaction is cancelled.

    Will set the state to CANCELLED or OVERRIDDEN

    :param tx_hash: Transaction hash of record to modify
    :type tx_hash: str, 0x-hex
    :param manual: If set, status will be OVERRIDDEN. Otherwise CANCELLED.
    :type manual: boolean
    :raises NotLocalTxError: If transaction not found in queue.
    """

    session = SessionBase.create_session()
    o = Otx.load(tx_hash, session=session)
    if o == None:
        session.close()
        raise NotLocalTxError('queue does not contain tx hash {}'.format(tx_hash))

    session.flush()

    try:
        if manual:
            o.override(session=session)
        else:
            o.cancel(session=session)
        session.commit()
    except TxStateChangeError as e:
        logg.exception('set cancel fail: {}'.format(e))
    except Exception as e:
        logg.exception('set cancel UNEXPECTED fail: {}'.format(e))
    session.close()

    return tx_hash


def set_rejected(tx_hash):
    """Used to set the status when the node rejects sending a transaction to network

    Will set the state to REJECTED

    :param tx_hash: Transaction hash of record to modify
    :type tx_hash: str, 0x-hex
    :raises NotLocalTxError: If transaction not found in queue.
    """

    session = SessionBase.create_session()
    o = Otx.load(tx_hash, session=session)
    if o == None:
        session.close()
        raise NotLocalTxError('queue does not contain tx hash {}'.format(tx_hash))

    session.flush()

    o.reject(session=session)
    session.commit()
    session.close()

    return tx_hash


def set_fubar(tx_hash):
    """Used to set the status when an unexpected error occurs.

    Will set the state to FUBAR

    :param tx_hash: Transaction hash of record to modify
    :type tx_hash: str, 0x-hex
    :raises NotLocalTxError: If transaction not found in queue.
    """

    session = SessionBase.create_session()
    o = Otx.load(tx_hash, session=session)
    if o == None:
        session.close()
        raise NotLocalTxError('queue does not contain tx hash {}'.format(tx_hash))

    session.flush()

    o.fubar(session=session)
    session.commit()
    session.close()

    return tx_hash


def set_manual(tx_hash):
    """Used to set the status when queue is manually changed

    Will set the state to MANUAL

    :param tx_hash: Transaction hash of record to modify
    :type tx_hash: str, 0x-hex
    :raises NotLocalTxError: If transaction not found in queue.
    """

    session = SessionBase.create_session()
    o = Otx.load(tx_hash, session=session)
    if o == None:
        session.close()
        raise NotLocalTxError('queue does not contain tx hash {}'.format(tx_hash))

    session.flush()

    o.manual(session=session)
    session.commit()
    session.close()

    return tx_hash


def set_ready(tx_hash):
    """Used to mark a transaction as ready to be sent to network

    :param tx_hash: Transaction hash of record to modify
    :type tx_hash: str, 0x-hex
    :raises NotLocalTxError: If transaction not found in queue.
    """
    session = SessionBase.create_session()
    o = Otx.load(tx_hash, session=session)
    if o == None:
        session.close()
        raise NotLocalTxError('queue does not contain tx hash {}'.format(tx_hash))
    session.flush()

    if o.status & StatusBits.GAS_ISSUES or is_nascent(o.status):
        o.readysend(session=session)
    else:
        o.retry(session=session)

    session.commit()
    session.close()

    return tx_hash


def set_reserved(tx_hash):
    session = SessionBase.create_session()
    o = Otx.load(tx_hash, session=session)
    if o == None:
        session.close()
        raise NotLocalTxError('queue does not contain tx hash {}'.format(tx_hash))

    session.flush()

    o.reserve(session=session)
    session.commit()
    session.close()

    return tx_hash



def set_waitforgas(tx_hash):
    """Used to set the status when a transaction must be deferred due to gas refill

    Will set the state to WAITFORGAS

    :param tx_hash: Transaction hash of record to modify
    :type tx_hash: str, 0x-hex
    :raises NotLocalTxError: If transaction not found in queue.
    """

    session = SessionBase.create_session()
    o = Otx.load(tx_hash, session=session)
    if o == None:
        session.close()
        raise NotLocalTxError('queue does not contain tx hash {}'.format(tx_hash))

    session.flush()

    o.waitforgas(session=session)
    session.commit()
    session.close()

    return tx_hash


def get_state_log(tx_hash):

    logs = []
    
    session = SessionBase.create_session()

    q = session.query(OtxStateLog)
    q = q.join(Otx)
    q = q.filter(Otx.tx_hash==strip_0x(tx_hash))
    q = q.order_by(OtxStateLog.date.asc())
    for l in q.all():
        logs.append((l.date, l.status,))

    session.close()

    return logs



def cancel_obsoletes_by_cache(tx_hash):
    session = SessionBase.create_session()
    q = session.query(
            Otx.nonce.label('nonce'),
            TxCache.sender.label('sender'),
            Otx.id.label('otxid'),
            )
    q = q.join(TxCache)
    q = q.filter(Otx.tx_hash==strip_0x(tx_hash))
    o = q.first()

    nonce = o.nonce
    sender = o.sender
    otxid = o.otxid

    q = session.query(Otx)
    q = q.join(TxCache)
    q = q.filter(Otx.nonce==nonce)
    q = q.filter(TxCache.sender==sender)
    q = q.filter(Otx.tx_hash!=strip_0x(tx_hash))

    for otwo in q.all():
        try:
            otwo.cancel(True, session=session)
        except TxStateChangeError as e:
            logg.exception('cancel non-final fail: {}'.format(e))
            session.close()
            raise(e)
        except Exception as e:
            logg.exception('cancel non-final UNEXPECTED fail: {}'.format(e))
            session.close()
            raise(e)
    session.commit()
    session.close()

    return tx_hash
