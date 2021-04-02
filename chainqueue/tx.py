# standard imports
import logging

# local imports
from chainqueue.db.models.otx import Otx
from chainqueue.db.models.tx import TxCache
from chainqueue.db.models.base import SessionBase
from chainqueue.db.enum import (
        StatusBits,
        )
from chainqueue.error import TxStateChangeError

logg = logging.getLogger().getChild(__name__)


def create(nonce, holder_address, tx_hash, signed_tx, chain_spec, obsolete_predecessors=True, session=None):
    """Create a new transaction queue record.

    :param nonce: Transaction nonce
    :type nonce: int
    :param holder_address: Sender address
    :type holder_address: str, 0x-hex
    :param tx_hash: Transaction hash
    :type tx_hash: str, 0x-hex
    :param signed_tx: Signed raw transaction
    :type signed_tx: str, 0x-hex
    :param chain_spec: Chain spec to create transaction for
    :type chain_spec: ChainSpec
    :returns: transaction hash
    :rtype: str, 0x-hash
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
