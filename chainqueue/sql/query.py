# TODO: this module could require better naming to discern what type of data the different methods return. Currently it's a mix of otx summary, otx objects, tx cache objects, tx representation dicts and hash/signedtx kv pairs

# standard imports
import logging
import time
import datetime

# external imports
from sqlalchemy import or_
from sqlalchemy import not_
from sqlalchemy import tuple_
from sqlalchemy import func
from hexathon import (
       add_0x,
       strip_0x,
       uniform as hex_uniform,
       )

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
        CacheIntegrityError,
        )

logg = logging.getLogger(__name__)


def get_tx_cache(chain_spec, tx_hash, session=None):
    """Returns an aggregate dictionary of outgoing transaction data and metadata

    :param chain_spec: Chain spec for transaction network
    :type chain_spec: chainlib.chain.ChainSpec
    :param tx_hash: Transaction hash of record to modify
    :type tx_hash: str, 0x-hex
    :param session: Backend state integrity session
    :type session: varies
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

    SessionBase.release_session(session)

    return tx


def get_tx(chain_spec, tx_hash, session=None):
    """Retrieve a transaction queue record by transaction hash

    :param chain_spec: Chain spec for transaction network
    :type chain_spec: chainlib.chain.ChainSpec
    :param tx_hash: Transaction hash of record to modify
    :type tx_hash: str, 0x-hex
    :param session: Backend state integrity session
    :type session: varies
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

    :param chain_spec: Chain spec for transaction network
    :type chain_spec: chainlib.chain.ChainSpec
    :param nonce: Nonce
    :type nonce: number
    :param sender: Ethereum address
    :type sender: str, 0x-hex
    :param decoder: Transaction decoder
    :type decoder: TODO - define transaction decoder
    :param session: Backend state integrity session
    :type session: varies
    :raises CacheIntegrityError: Cached data does not match intepreted data.
    :returns: Transactions
    :rtype: dict, with transaction hash as key, signed raw transaction as value
    """
    sender = add_0x(hex_uniform(strip_0x(sender)))

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
            tx_from = add_0x(hex_uniform(strip_0x(tx['from'])))
            if sender != None and tx_from != sender:
                raise CacheIntegrityError('Cache sender {} does not match sender {} in tx {} using decoder {}'.format(sender, tx_from, r.tx_hash, str(decoder)))
        txs[r.tx_hash] = r.signed_tx

    SessionBase.release_session(session)

    return txs


def get_paused_tx_cache(chain_spec, status=None, sender=None, session=None, decoder=None):
    """Returns not finalized transactions that have been attempted sent without success.

    :param chain_spec: Chain spec for transaction network
    :type chain_spec: chainlib.chain.ChainSpec
    :param status: If set, will return transactions with this local queue status only
    :type status: cic_eth.db.enum.StatusEnum
    :param sender: Sender address to return transactions for
    :type sender: str
    :param session: Backend state integrity session
    :type session: varies
    :param decoder: Transaction decoder
    :type decoder: Function accepting signed transaction data as input
    :raises ValueError: Status is finalized, sent or never attempted sent
    :returns: Key value pairs with transaction hash and signed raw transaction
    :rtype: dict
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
        sender = add_0x(hex_uniform(strip_0x(sender)))
        q = q.filter(TxCache.sender==sender)

    txs = {}
    gas = 0

    for r in q.all():
        tx_signed_bytes = bytes.fromhex(r.signed_tx)
        if decoder != None:
            tx = decoder(tx_signed_bytes, chain_spec)
            tx_from = add_0x(hex_uniform(strip_0x(tx['from'])))
            if sender != None and tx_from != sender:
                raise CacheIntegrityError('Cache sender {} does not match sender {} in tx {} using decoder {}'.format(sender, tx_from, r.tx_hash, str(decoder)))
            gas += tx['gas'] * tx['gasPrice']

        txs[r.tx_hash] = r.signed_tx

    SessionBase.release_session(session)

    return txs


def get_status_tx_cache(chain_spec, status, not_status=None, before=None, exact=False, limit=0, session=None, decoder=None):
    """Retrieve transaction with a specific queue status.

    :param chain_spec: Chain spec for transaction network
    :type chain_spec: chainlib.chain.ChainSpec
    :param status: Status to match transactions with
    :type status: str
    :param before: If set, return only transactions older than the timestamp
    :type before: datetime.dateTime
    :param exact: If set, will match exact status value. If not set, will match any of the status bits set
    :type exact: bool
    :param limit: Limit amount of returned transactions
    :type limit: number
    :param decoder: Transaction decoder
    :type decoder: TODO - define transaction decoder
    :param session: Backend state integrity session
    :type session: varies
    :returns: Transactions
    :rtype: list of cic_eth.db.models.otx.Otx
    """
    txs = {}
    session = SessionBase.bind_session(session)
    q = session.query(Otx)
    q = q.join(TxCache)
    if before != None:
        q = q.filter(Otx.date_updated<before)
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

    :param chain_spec: Chain spec for transaction network
    :type chain_spec: chainlib.chain.ChainSpec
    :param status: Defines the status used to filter as upcoming.
    :type status: cic_eth.db.enum.StatusEnum
    :param not_status: Invalidates any matches matching one of the given bits
    :type not_status: cic_eth.db.enum.StatusEnum
    :param recipient: Ethereum address of recipient to return transaction for
    :type recipient: str, 0x-hex
    :param before: Only return transactions if their modification date is older than the given timestamp
    :type before: datetime.datetime
    :param limit: Limit amount of returned transactions
    :type limit: number
    :param decoder: Transaction decoder
    :type decoder: TODO - define transaction decoder
    :param session: Backend state integrity session
    :type session: varies
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

        tx_signed_bytes = bytes.fromhex(strip_0x(o.signed_tx))
        tx = decoder(tx_signed_bytes, chain_spec)
        txs[o.tx_hash] = o.signed_tx
        
        q = session.query(TxCache)
        q = q.filter(TxCache.otx_id==o.id)
        o = q.first()

        o.date_checked = datetime.datetime.utcnow()
        session.add(o)
        session.commit()

        i += 1
        if limit > 0 and limit == i:
            break

    SessionBase.release_session(session)

    return txs


def sql_range_filter(session, criteria=None):
    """Convert an arbitrary type to a sql query range

    :param session: Backend state integrity session
    :type session: varies
    :param criteria: Range criteria
    :type criteria: any
    :raises NotLocalTxError: If criteria is string, transaction hash does not exist in backend
    :rtype: tuple
    :returns: type string identifier, value
    """
    boundary = None
    
    if criteria == None:
        return None

    if isinstance(criteria, str):
        q = session.query(Otx)
        q = q.filter(Otx.tx_hash==strip_0x(criteria))
        r = q.first()
        if r == None:
            raise NotLocalTxError('unknown tx hash as bound criteria specified: {}'.format(criteria))
        boundary = ('id', r.id,)
    elif isinstance(criteria, int):
        boundary = ('id', criteria,)
    elif isinstance(criteria, datetime.datetime):
        boundary = ('date', criteria,)   

    return boundary


def get_account_tx(chain_spec, address, as_sender=True, as_recipient=True, counterpart=None, since=None, until=None, status=None, not_status=None, status_target=None, session=None):
    """Returns all local queue transactions for a given Ethereum address

    The since parameter effect depends on its type. Results are returned inclusive of the given parameter condition.

    * str - transaction hash; all transactions added after the given hash
    * int - all transactions after the given db insert id
    * datetime.datetime - all transactions added since the given datetime

    :param chain_spec: Chain spec for transaction network
    :type chain_spec: chainlib.chain.ChainSpec
    :param address: Ethereum address
    :type address: str, 0x-hex
    :param as_sender: If False, will omit transactions where address is sender
    :type as_sender: bool
    :param as_recipient: If False, will omit transactions where address is recipient
    :type as_recipient: bool
    :param counterpart: Only return transactions where this Ethereum address is the other end of the transaction (not in use)
    :type counterpart: str, 0x-hex
    :param since: Only include transactions submitted before this datetime
    :type since: datetime
    :param until: Only include transactions submitted before this datetime
    :type until: datetime
    :param status: Only include transactions where the given status bits are set
    :type status: chainqueue.enum.StatusEnum
    :param not_status: Only include transactions where the given status bits are not set
    :type not_status: chainqueue.enum.StatusEnum
    :param status_target: Only include transaction where the status argument is exact match
    :type status_target: chainqueue.enum.StatusEnum
    :param session: Backend state integrity session
    :type session: varies
    :raises ValueError: If address is set to be neither sender nor recipient
    :returns: Transactions 
    :rtype: dict, with transaction hash as key, signed raw transaction as value
    """
    if not as_sender and not as_recipient:
        raise ValueError('at least one of as_sender and as_recipient must be True')

    txs = {}

    session = SessionBase.bind_session(session)
    address = add_0x(hex_uniform(strip_0x(address)))

    try:
        filter_offset = sql_range_filter(session, criteria=since)
        filter_limit = sql_range_filter(session, criteria=until)
    except NotLocalTxError as e:
        logg.error('query build failed: {}'.format(e))
        return {}

    q = session.query(Otx)
    q = q.join(TxCache)
    if as_sender and as_recipient:
        q = q.filter(or_(TxCache.sender==address, TxCache.recipient==address))
    elif as_sender:
        q = q.filter(TxCache.sender==address)
    else:
        q = q.filter(TxCache.recipient==address)

    if filter_offset != None:
        if filter_offset[0] == 'id':
            q = q.filter(Otx.id>=filter_offset[1])
        elif filter_offset[0] == 'date':
            q = q.filter(Otx.date_created>=filter_offset[1])

    if filter_limit != None:
        if filter_limit[0] == 'id':
            q = q.filter(Otx.id<=filter_limit[1])
        elif filter_limit[0] == 'date':
            q = q.filter(Otx.date_created<=filter_limit[1])

    if status != None:
        if status_target == None:
            status_target = status
        q = q.filter(Otx.status.op('&')(status)==status_target)
    
    if not_status != None:
        q = q.filter(Otx.status.op('&')(not_status)==0)

    q = q.order_by(Otx.nonce.asc(), Otx.date_created.asc())

    results = q.all()
    for r in results:
        if txs.get(r.tx_hash) != None:
            logg.debug('tx {} already recorded'.format(r.tx_hash))
            continue
        txs[r.tx_hash] = r.signed_tx

    SessionBase.release_session(session)

    return txs


def count_tx(chain_spec, sender=None, status=None, status_target=None, session=None):
    """Count transaction records matching the given criteria.
    
    :param chain_spec: Chain spec for transaction network
    :type chain_spec: chainlib.chain.ChainSpec
    :param sender: Sender address to count transactions for
    :type sender: str
    :param status: Status to count transactions for
    :type status: chainqueue.enum.StatusEnum
    :param status_target: If set, will match status argument exactly against the given value
    :type status_target: chainqueue.enum.StatusEnum
    :param session: Backend state integrity session
    :type session: varies
    :rtype: int
    :returns: Transaction count
    """
    session = SessionBase.bind_session(session)
    q = session.query(Otx.id)
    q = q.join(TxCache)
    if status != None:
        if status_target == None:
            status_target = status
        q = q.filter(Otx.status.op('&')(status)==status_target)
    if sender != None:
        q = q.filter(TxCache.sender==sender)
    result = q.count()
    SessionBase.release_session(session)
    return result
