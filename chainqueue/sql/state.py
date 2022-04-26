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


def set_sent(chain_spec, tx_hash, fail=False, session=None):
    """Used to set the status after a send attempt

    :param chain_spec: Chain spec for transaction network
    :type chain_spec: chainlib.chain.ChainSpec
    :param tx_hash: Transaction hash of record to modify
    :type tx_hash: str, 0x-hex
    :param fail: if True, will set a SENDFAIL status, otherwise a SENT status. (Default: False)
    :type fail: boolean
    :param session: Backend state integrity session
    :type session: varies
    :raises NotLocalTxError: If transaction not found in queue.
    :returns: True if tx is known, False otherwise
    :rtype: boolean
    """
    session = SessionBase.bind_session(session)
    o = Otx.load(tx_hash, session=session)
    if o == None:
        logg.warning('not local tx, skipping {}'.format(tx_hash))
        SessionBase.release_session(session)
        return False

    try:
        if fail:
            o.sendfail(session=session)
        else:
            o.sent(session=session)
    except TxStateChangeError as e:
        logg.exception('set sent fail: {}'.format(e))
        SessionBase.release_session(session)
        raise(e)
    except Exception as e:
        logg.exception('set sent UNEXPECED fail: {}'.format(e))
        SessionBase.release_session(session)
        raise(e)

    session.commit()
    SessionBase.release_session(session)

    return tx_hash


def set_final(chain_spec, tx_hash, block=None, tx_index=None, fail=False, session=None):
    """Used to set the status of an incoming transaction result. 

    :param chain_spec: Chain spec for transaction network
    :type chain_spec: chainlib.chain.ChainSpec
    :param tx_hash: Transaction hash of record to modify
    :type tx_hash: str, 0x-hex
    :param block: Block number if final status represents a confirmation on the network
    :type block: number
    :param tx_index: Transaction index if final status represents a confirmation on the network
    :type tx_index: number
    :param fail: if True, will set a SUCCESS status, otherwise a REVERTED status. (Default: False)
    :type fail: boolean
    :param session: Backend state integrity session
    :type session: varies
    :raises NotLocalTxError: If transaction not found in queue.
    :rtype: str
    :returns: Transaction hash, in hex
    """
    session = SessionBase.bind_session(session)
    o = Otx.load(tx_hash, session=session)
    
    if o == None:
        SessionBase.release_session(session)
        raise NotLocalTxError('queue does not contain tx hash {}'.format(tx_hash))

    session.flush()

    try:
        if fail:
            o.minefail(block, session=session)
        else:
            o.success(block, session=session)
    except TxStateChangeError as e:
        logg.exception('set final fail: {}'.format(e))
        SessionBase.release_session(session)
        raise(e)
    except Exception as e:
        logg.exception('set final UNEXPECTED fail: {}'.format(e))
        SessionBase.release_session(session)
        raise(e)

    if block != None:
        try:
            TxCache.set_final(o.tx_hash, block, tx_index, session=session)
        except NotLocalTxError:
            logg.debug('otx for {} does not have cache complement'.format(tx_hash))

    session.commit()

    SessionBase.release_session(session)

    return tx_hash
    

def set_cancel(chain_spec, tx_hash, manual=False, session=None):
    """Used to set the status when a transaction is cancelled.

    Will set the state to CANCELLED or OVERRIDDEN

    :param chain_spec: Chain spec for transaction network
    :type chain_spec: chainlib.chain.ChainSpec
    :param tx_hash: Transaction hash of record to modify
    :type tx_hash: str, 0x-hex
    :param manual: If set, status will be OVERRIDDEN. Otherwise CANCELLED.
    :type manual: boolean
    :param session: Backend state integrity session
    :type session: varies
    :raises NotLocalTxError: If transaction not found in queue.
    :rtype: str
    :returns: Transaction hash, in hex
    """
    session = SessionBase.bind_session(session)
    o = Otx.load(tx_hash, session=session)
    if o == None:
        SessionBase.release_session(session)
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
    SessionBase.release_session(session)

    return tx_hash


def set_rejected(chain_spec, tx_hash, session=None):
    """Used to set the status when the node rejects sending a transaction to network

    Will set the state to REJECTED

    :param chain_spec: Chain spec for transaction network
    :type chain_spec: chainlib.chain.ChainSpec
    :param tx_hash: Transaction hash of record to modify
    :type tx_hash: str, 0x-hex
    :param session: Backend state integrity session
    :type session: varies
    :raises NotLocalTxError: If transaction not found in queue.
    :rtype: str
    :returns: Transaction hash, in hex
    """

    session = SessionBase.bind_session(session)
    o = Otx.load(tx_hash, session=session)
    if o == None:
        SessionBase.release_session(session)
        raise NotLocalTxError('queue does not contain tx hash {}'.format(tx_hash))

    session.flush()

    o.reject(session=session)
    session.commit()
    SessionBase.release_session(session)

    return tx_hash


def set_fubar(chain_spec, tx_hash, session=None):
    """Used to set the status when an unexpected error occurs.

    Will set the state to FUBAR

    :param chain_spec: Chain spec for transaction network
    :type chain_spec: chainlib.chain.ChainSpec
    :param tx_hash: Transaction hash of record to modify
    :type tx_hash: str, 0x-hex
    :param session: Backend state integrity session
    :type session: varies
    :raises NotLocalTxError: If transaction not found in queue.
    :rtype: str
    :returns: Transaction hash, in hex
    """

    session = SessionBase.bind_session(session)
    o = Otx.load(tx_hash, session=session)
    if o == None:
        SessionBase.release_session(session)
        raise NotLocalTxError('queue does not contain tx hash {}'.format(tx_hash))

    session.flush()

    o.fubar(session=session)
    session.commit()
    SessionBase.release_session(session)

    return tx_hash


def set_manual(chain_spec, tx_hash, session=None):
    """Used to set the status when queue is manually changed

    Will set the state to MANUAL

    :param chain_spec: Chain spec for transaction network
    :type chain_spec: chainlib.chain.ChainSpec
    :param tx_hash: Transaction hash of record to modify
    :type tx_hash: str, 0x-hex
    :param session: Backend state integrity session
    :type session: varies
    :raises NotLocalTxError: If transaction not found in queue.
    :rtype: str
    :returns: Transaction hash, in hex
    """

    session = SessionBase.bind_session(session)
    o = Otx.load(tx_hash, session=session)
    if o == None:
        SessionBase.release_session(session)
        raise NotLocalTxError('queue does not contain tx hash {}'.format(tx_hash))

    session.flush()

    o.manual(session=session)
    session.commit()
    SessionBase.release_session(session)

    return tx_hash


def set_ready(chain_spec, tx_hash, session=None):
    """Used to mark a transaction as ready to be sent to network

    :param chain_spec: Chain spec for transaction network
    :type chain_spec: chainlib.chain.ChainSpec
    :param tx_hash: Transaction hash of record to modify
    :type tx_hash: str, 0x-hex
    :param session: Backend state integrity session
    :type session: varies
    :raises NotLocalTxError: If transaction not found in queue.
    :rtype: str
    :returns: Transaction hash, in hex
    """
    session = SessionBase.bind_session(session)
    o = Otx.load(tx_hash, session=session)
    if o == None:
        SessionBase.release_session(session)
        raise NotLocalTxError('queue does not contain tx hash {}'.format(tx_hash))
    session.flush()

    if o.status & StatusBits.GAS_ISSUES or is_nascent(o.status):
        o.readysend(session=session)
    else:
        o.retry(session=session)

    session.commit()
    SessionBase.release_session(session)

    return tx_hash


def set_reserved(chain_spec, tx_hash, session=None):
    """Used to mark a transaction as reserved by a worker for processing.

    :param chain_spec: Chain spec for transaction network
    :type chain_spec: chainlib.chain.ChainSpec
    :param tx_hash: Transaction hash of record to modify
    :type tx_hash: str, 0x-hex
    :param session: Backend state integrity session
    :type session: varies
    :raises NotLocalTxError: If transaction not found in queue.
    """

    session = SessionBase.bind_session(session)
    o = Otx.load(tx_hash, session=session)
    if o == None:
        SessionBase.release_session(session)
        raise NotLocalTxError('queue does not contain tx hash {}'.format(tx_hash))

    session.flush()

    o.reserve(session=session)
    session.commit()
    SessionBase.release_session(session)

    return tx_hash



def set_waitforgas(chain_spec, tx_hash, session=None):
    """Used to set the status when a transaction must be deferred due to gas refill

    Will set the state to WAITFORGAS

    :param chain_spec: Chain spec for transaction network
    :type chain_spec: chainlib.chain.ChainSpec
    :param tx_hash: Transaction hash of record to modify
    :type tx_hash: str, 0x-hex
    :param session: Backend state integrity session
    :type session: varies
    :raises NotLocalTxError: If transaction not found in queue.
    :rtype: str
    :returns: Transaction hash, in hex
    """
    session = SessionBase.bind_session(session)
    o = Otx.load(tx_hash, session=session)
    if o == None:
        SessionBase.release_session(session)
        raise NotLocalTxError('queue does not contain tx hash {}'.format(tx_hash))

    session.flush()

    o.waitforgas(session=session)
    session.commit()
    SessionBase.release_session(session)

    return tx_hash


def get_state_log(chain_spec, tx_hash, session=None):
    """If state log is activated, retrieves all state log changes for the given transaction.

    :param chain_spec: Chain spec for transaction network
    :type chain_spec: chainlib.chain.ChainSpec
    :param tx_hash: Transaction hash of record to modify
    :type tx_hash: str, 0x-hex
    :param session: Backend state integrity session
    :type session: varies
    :raises NotLocalTxError: If transaction not found in queue.
    :rtype: list
    :returns: Log items
    """
    logs = []
    
    session = SessionBase.bind_session(session)

    q = session.query(OtxStateLog)
    q = q.join(Otx)
    q = q.filter(Otx.tx_hash==strip_0x(tx_hash))
    q = q.order_by(OtxStateLog.date.asc())
    for l in q.all():
        logs.append((l.date, l.status,))

    SessionBase.release_session(session)

    return logs



def obsolete_by_cache(chain_spec, tx_hash, final, session=None):
    """Explicitly obsolete single transaction by transaction with same nonce.

    :param chain_spec: Chain spec for transaction network
    :type chain_spec: chainlib.chain.ChainSpec
    :param tx_hash: Transaction hash of record to modify, in hex
    :type tx_hash: str
    :param final: Transaction hash superseding record, in hex
    :type final: str
    :param session: Backend state integrity session
    :type session: varies
    :raises TxStateChangeError: Transaction is not obsoletable
    :rtype: str
    :returns: Transaction hash, in hex
    """
    session = SessionBase.bind_session(session)

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
    q = q.filter(Otx.id!=otxid)

    for otwo in q.all():
        try:
            otwo.cancel(final, session=session)
            logg.debug('cancel {} final {}'.format(tx_hash, final))
        except TxStateChangeError as e:
            logg.exception('cancel non-final fail: {}'.format(e))
            session.close()
            raise(e)
        except Exception as e:
            logg.exception('cancel non-final UNEXPECTED fail: {}'.format(e))
            session.close()
            raise(e)
    session.commit()

    SessionBase.release_session(session)

    return tx_hash


def set_checked(chain_spec, tx_hash, session=None):
    """Set the checked date for the transaction to current datetime

    :param chain_spec: Chain spec for transaction network
    :type chain_spec: chainlib.chain.ChainSpec
    :param tx_hash: Transaction hash of record to modify
    :type tx_hash: str, 0x-hex
    :param session: Backend state integrity session
    :type session: varies
    :raises NotLocalTxError: If transaction not found in queue.
    :rtype: str
    :returns: Transaction hash, in hex
    """

    session = SessionBase.bind_session(session)
    o = TxCache.load(tx_hash, session=session)
    if o == None:
        SessionBase.release_session(session)
        raise NotLocalTxError('queue does not contain tx hash {}'.format(tx_hash))

    session.flush()

    o.check()
    session.add(o)
    session.commit()
    SessionBase.release_session(session)

    return tx_hash
