# standard imports
import logging
import time
import datetime

# external imports
from sqlalchemy import or_
from sqlalchemy import not_
from sqlalchemy import tuple_
from sqlalchemy import func
from hexathon import add_0x

# local imports
from chainqueue.db.models.otx import Otx
from chainqueue.db.models.tx import TxCache
from chainqueue.db.models.base import SessionBase
from chainqueue.db.enum import status_str
from chainqueue.db.enum import (
        StatusEnum,
        StatusBits,
        is_alive,
        dead,
        )
from chainqueue.error import (
        NotLocalTxError,
        )

logg = logging.getLogger().getChild(__name__)


def get_tx_cache(chain_spec, tx_hash, session=None):
    """Returns an aggregate dictionary of outgoing transaction data and metadata

    :param tx_hash: Transaction hash of record to modify
    :type tx_hash: str, 0x-hex
    :raises NotLocalTxError: If transaction not found in queue.
    :returns: Transaction data
    :rtype: dict
    """
    session = SessionBase.bind_session(session)

    otx = Otx.load(tx_hash, session=session)
    if otx == None:
        SessionBase.release_session(session)
        raise NotLocalTxError(tx_hash)

    session.flush()

    q = session.query(TxCache)
    q = q.filter(TxCache.otx_id==otx.id)
    txc = q.first()

    SessionBase.release_session(session)

    # TODO: DRY, get_tx_cache / get_tx
    tx = {
        'tx_hash': add_0x(otx.tx_hash),
        'signed_tx': add_0x(otx.signed_tx),
        'nonce': otx.nonce,
        'status': status_str(otx.status),
        'status_code': otx.status,
        'source_token': add_0x(txc.source_token_address),
        'destination_token': add_0x(txc.destination_token_address),
        'block_number': otx.block,
        'tx_index': txc.tx_index,
        'sender': add_0x(txc.sender),
        'recipient': add_0x(txc.recipient),
        'from_value': int(txc.from_value),
        'to_value': int(txc.to_value),
        'date_created': txc.date_created,
        'date_updated': txc.date_updated,
        'date_checked': txc.date_checked,
            }

    return tx


def get_tx(chain_spec, tx_hash, session=None):
    """Retrieve a transaction queue record by transaction hash

    :param tx_hash: Transaction hash of record to modify
    :type tx_hash: str, 0x-hex
    :raises NotLocalTxError: If transaction not found in queue.
    :returns: nonce, address and signed_tx (raw signed transaction)
    :rtype: dict
    """
    session = SessionBase.bind_session(session)
    otx = Otx.load(tx_hash, session=session)
    if otx == None:
        SessionBase.release_session(session)
        raise NotLocalTxError('queue does not contain tx hash {}'.format(tx_hash))

    o = {
        'otx_id': otx.id,
        'nonce': otx.nonce,
        'signed_tx': otx.signed_tx,
        'status': otx.status,
            }
    logg.debug('get tx {}'.format(o))
    SessionBase.release_session(session)
    return o


def get_nonce_tx_cache(chain_spec, nonce, sender, decoder=None, session=None):
    """Retrieve all transactions for address with specified nonce

    :param nonce: Nonce
    :type nonce: number
    :param address: Ethereum address
    :type address: str, 0x-hex
    :returns: Transactions
    :rtype: dict, with transaction hash as key, signed raw transaction as value
    """
    session = SessionBase.bind_session(session)
    q = session.query(Otx)
    q = q.join(TxCache)
    q = q.filter(TxCache.sender==sender)
    q = q.filter(Otx.nonce==nonce)
   
    txs = {}
    for r in q.all():
        tx_signed_bytes = bytes.fromhex(r.signed_tx)
        if decoder != None:
            tx = decoder(tx_signed_bytes, chain_spec)
            if sender != None and tx['from'] != sender:
                raise IntegrityError('Cache sender {} does not match sender in tx {} using decoder {}'.format(sender, r.tx_hash, str(decoder)))
        txs[r.tx_hash] = r.signed_tx

    SessionBase.release_session(session)

    return txs


def get_paused_tx_cache(chain_spec, status=None, sender=None, session=None, decoder=None):
    """Returns not finalized transactions that have been attempted sent without success.

    :param status: If set, will return transactions with this local queue status only
    :type status: cic_eth.db.enum.StatusEnum
    :param recipient: Recipient address to return transactions for
    :type recipient: str, 0x-hex
    :param chain_id: Numeric chain id to use to parse signed transaction data
    :type chain_id: number
    :raises ValueError: Status is finalized, sent or never attempted sent
    :returns: Transactions
    :rtype: dict, with transaction hash as key, signed raw transaction as value
    """
    session = SessionBase.bind_session(session)
    q = session.query(Otx)

    if status != None:
        if status == StatusEnum.PENDING or status & StatusBits.IN_NETWORK or not is_alive(status):
            SessionBase.release_session(session)
            raise ValueError('not a valid paused tx value: {}'.format(status))
        q = q.filter(Otx.status.op('&')(status.value)==status.value)
        q = q.join(TxCache)
    else:
        q = q.filter(Otx.status>StatusEnum.PENDING.value)
        q = q.filter(not_(Otx.status.op('&')(StatusBits.IN_NETWORK.value)>0))

    if sender != None:
        q = q.filter(TxCache.sender==sender)

    txs = {}
    gas = 0

    for r in q.all():
        tx_signed_bytes = bytes.fromhex(r.signed_tx)
        if decoder != None:
            tx = decoder(tx_signed_bytes, chain_spec)
            if sender != None and tx['from'] != sender:
                raise IntegrityError('Cache sender {} does not match sender in tx {} using decoder {}'.format(sender, r.tx_hash, str(decoder)))
            gas += tx['gas'] * tx['gasPrice']

        txs[r.tx_hash] = r.signed_tx

    SessionBase.release_session(session)

    return txs


def get_status_tx_cache(chain_spec, status, not_status=None, before=None, exact=False, limit=0, session=None, decoder=None):
    """Retrieve transaction with a specific queue status.

    :param status: Status to match transactions with
    :type status: str
    :param before: If set, return only transactions older than the timestamp
    :type status: datetime.dateTime
    :param limit: Limit amount of returned transactions
    :type limit: number
    :returns: Transactions
    :rtype: list of cic_eth.db.models.otx.Otx
    """
    txs = {}
    session = SessionBase.bind_session(session)
    q = session.query(Otx)
    q = q.join(TxCache)
    if before != None:
        q = q.filter(TxCache.date_updated<before)
    if exact:
        q = q.filter(Otx.status==status)
    else:
        q = q.filter(Otx.status.op('&')(status)>0)
        if not_status != None:
            q = q.filter(Otx.status.op('&')(not_status)==0)
    q = q.order_by(Otx.nonce.asc(), Otx.date_created.asc())
    i = 0
    for o in q.all():
        if limit > 0 and i == limit:
            break
        txs[o.tx_hash] = o.signed_tx
        i += 1
    SessionBase.release_session(session)
    return txs


def get_upcoming_tx(chain_spec, status=StatusEnum.READYSEND, not_status=None, recipient=None, before=None, limit=0, session=None, decoder=None):
    """Returns the next pending transaction, specifically the transaction with the lowest nonce, for every recipient that has pending transactions.

    Will omit addresses that have the LockEnum.SEND bit in Lock set.

    (TODO) Will not return any rows if LockEnum.SEND bit in Lock is set for zero address.

    :param status: Defines the status used to filter as upcoming.
    :type status: cic_eth.db.enum.StatusEnum
    :param recipient: Ethereum address of recipient to return transaction for
    :type recipient: str, 0x-hex
    :param before: Only return transactions if their modification date is older than the given timestamp
    :type before: datetime.datetime
    :param chain_id: Chain id to use to parse signed transaction data
    :type chain_id: number
    :raises ValueError: Status is finalized, sent or never attempted sent
    :returns: Transactions
    :rtype: dict, with transaction hash as key, signed raw transaction as value
    """
    session = SessionBase.bind_session(session)
    q_outer = session.query(
            TxCache.sender,
            func.min(Otx.nonce).label('nonce'),
            )
    q_outer = q_outer.join(TxCache)

    if not is_alive(status):
        SessionBase.release_session(session)
        raise ValueError('not a valid non-final tx value: {}'.format(status))
    if status == StatusEnum.PENDING:
        q_outer = q_outer.filter(Otx.status==status.value)
    else:
        q_outer = q_outer.filter(Otx.status.op('&')(status)==status)

    if not_status != None:
        q_outer = q_outer.filter(Otx.status.op('&')(not_status)==0)

    if recipient != None:
        q_outer = q_outer.filter(TxCache.recipient==recipient)

    q_outer = q_outer.group_by(TxCache.sender)

    txs = {}

    i = 0
    for r in q_outer.all():
        q = session.query(Otx)
        q = q.join(TxCache)
        q = q.filter(TxCache.sender==r.sender)
        q = q.filter(Otx.nonce==r.nonce)

        if before != None:
            q = q.filter(TxCache.date_checked<before)
       
        q = q.order_by(TxCache.date_created.desc())
        o = q.first()

        # TODO: audit; should this be possible if a row is found in the initial query? If not, at a minimum log error.
        if o == None:
            continue

        tx_signed_bytes = bytes.fromhex(o.signed_tx[2:])
        tx = decoder(tx_signed_bytes, chain_spec)
        txs[o.tx_hash] = o.signed_tx
        
        q = session.query(TxCache)
        q = q.filter(TxCache.otx_id==o.id)
        o = q.first()

        o.date_checked = datetime.datetime.now()
        session.add(o)
        session.commit()

        i += 1
        if limit > 0 and limit == i:
            break

    SessionBase.release_session(session)

    return txs


def get_account_tx(chain_spec, address, as_sender=True, as_recipient=True, counterpart=None, session=None):
    """Returns all local queue transactions for a given Ethereum address

    :param address: Ethereum address
    :type address: str, 0x-hex
    :param as_sender: If False, will omit transactions where address is sender
    :type as_sender: bool
    :param as_sender: If False, will omit transactions where address is recipient
    :type as_sender: bool
    :param counterpart: Only return transactions where this Ethereum address is the other end of the transaction (not in use)
    :type counterpart: str, 0x-hex
    :raises ValueError: If address is set to be neither sender nor recipient
    :returns: Transactions 
    :rtype: dict, with transaction hash as key, signed raw transaction as value
    """
    if not as_sender and not as_recipient:
        raise ValueError('at least one of as_sender and as_recipient must be True')

    txs = {}

    session = SessionBase.bind_session(session)
    q = session.query(Otx)
    q = q.join(TxCache)
    if as_sender and as_recipient:
        q = q.filter(or_(TxCache.sender==address, TxCache.recipient==address))
    elif as_sender:
        q = q.filter(TxCache.sender==address)
    else:
        q = q.filter(TxCache.recipient==address)
    q = q.order_by(Otx.nonce.asc(), Otx.date_created.asc()) 

    results = q.all()
    for r in results:
        if txs.get(r.tx_hash) != None:
            logg.debug('tx {} already recorded'.format(r.tx_hash))
            continue
        txs[r.tx_hash] = r.signed_tx

    SessionBase.release_session(session)

    return txs
