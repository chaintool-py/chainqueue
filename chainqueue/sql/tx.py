# standard imports
import logging

# external imports
from hexathon import (
        uniform as hex_uniform,
        add_0x,
        strip_0x,
        )

# local imports
from chainqueue.db.models.otx import Otx
from chainqueue.db.models.tx import TxCache
from chainqueue.db.models.base import SessionBase
from chainqueue.db.enum import (
        StatusBits,
        )
from chainqueue.error import TxStateChangeError

logg = logging.getLogger().getChild(__name__)


def create(chain_spec, nonce, holder_address, tx_hash, signed_tx, obsolete_predecessors=True, session=None):
    """Create a new transaction queue record.

    :param chain_spec: Chain spec of transaction network
    :type chain_spec: chainlib.chain.ChainSpec
    :param nonce: Transaction nonce
    :type nonce: int
    :param holder_address: Sender address
    :type holder_address: str, 0x-hex
    :param tx_hash: Transaction hash
    :type tx_hash: str, 0x-hex
    :param signed_tx: Signed raw transaction
    :type signed_tx: str, 0x-hex
    :param obsolete_predecessors: If true will mark all other transactions with the same nonce as obsolete (should not be retried)
    :type obsolete_predecessors: bool
    :param session: Backend state integrity session
    :type session: varies
    :raises TxStateChangeError: Transaction obsoletion failed
    :returns: transaction hash, in hex
    :rtype: str
    """
    session = SessionBase.bind_session(session)

    o = Otx.add(
            nonce=nonce,
            tx_hash=tx_hash,
            signed_tx=signed_tx,
            session=session,
            )
    session.flush()

    # TODO: No magic, please, should be separate step
    if obsolete_predecessors:
        q = session.query(Otx)
        q = q.join(TxCache)
        q = q.filter(Otx.nonce==nonce)
        q = q.filter(TxCache.sender==holder_address)
        q = q.filter(Otx.tx_hash!=tx_hash)
        q = q.filter(Otx.status.op('&')(StatusBits.FINAL)==0)

        for otx in q.all():
            logg.info('otx {} obsoleted by {}'.format(otx.tx_hash, tx_hash))
            try:
                otx.cancel(confirmed=False, session=session)
            except TxStateChangeError as e:
                logg.exception('obsolete fail: {}'.format(e))
                session.close()
                raise(e)
            except Exception as e:
                logg.exception('obsolete UNEXPECTED fail: {}'.format(e))
                session.close()
                raise(e)

    session.commit()
    SessionBase.release_session(session)
    logg.debug('queue created nonce {} from {} hash {}'.format(nonce, holder_address, tx_hash))
    return tx_hash


def cache_tx_dict(tx_dict, session=None):
    """Add a transaction cache entry to backend.

    :param tx_dict: Transaction cache details
    :type tx_dict: dict
    :param session: Backend state integrity session
    :type session: varies
    :rtype: tuple
    :returns: original transaction, backend insertion id
    """
    session = SessionBase.bind_session(session)

    txc = TxCache(
        tx_dict['hash'],
        tx_dict['from'],
        tx_dict['to'],
        tx_dict['source_token'],
        tx_dict['destination_token'],
        tx_dict['from_value'],
        tx_dict['to_value'],
        session=session
        )
    
    session.add(txc)
    session.commit()

    insert_id = txc.id

    SessionBase.release_session(session)

    return (tx_dict, insert_id)
