# standard imports
import datetime

# external imports
from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, Boolean, NUMERIC
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from hexathon import (
        strip_0x,
        )

# local imports
from .base import SessionBase
from .otx import Otx
from chainqueue.error import (
        NotLocalTxError,
        TxStateChangeError,
        )


class TxCache(SessionBase):
    """Metadata expansions for outgoing transactions.

    These records are not essential for handling of outgoing transaction queues. It is implemented to reduce the amount of computation spent of parsing and analysing raw signed transaction data.

    Instantiation of the object will fail if an outgoing transaction record with the same transaction hash does not exist.

    Typically three types of transactions are recorded:

    - Token transfers; where source and destination token values and addresses are identical, sender and recipient differ.
    - Token conversions; source and destination token values and addresses differ, sender and recipient are identical.
    - Any other transaction; source and destination token addresses are zero-address.

    :param tx_hash: Transaction hash
    :type tx_hash: str, 0x-hex
    :param sender: Ethereum address of transaction sender
    :type sender: str, 0x-hex
    :param recipient: Ethereum address of transaction beneficiary (e.g. token transfer recipient)
    :type recipient: str, 0x-hex
    :param source_token_address: Contract address of token that sender spent from
    :type source_token_address: str, 0x-hex
    :param destination_token_address: Contract address of token that recipient will receive balance of
    :type destination_token_address: str, 0x-hex
    :param from_value: Amount of source tokens spent
    :type from_value: number
    :param to_value: Amount of destination tokens received
    :type to_value: number
    :param block_number: Block height the transaction was mined at, or None if not yet mined
    :type block_number: number or None
    :param tx_number: Transaction index in the block the transaction was mined in, or None if not yet mined
    :type tx_number: number or None
    :raises NotLocalTxError: Outgoing transaction for given transaction hash does not exist
    """
    __tablename__ = 'tx_cache'

    otx_id = Column(Integer, ForeignKey('otx.id'))
    """Foreign key to chainqueue.db.models.otx.Otx"""
    source_token_address = Column(String(42))
    """Contract address of token that sender spent from"""
    destination_token_address = Column(String(42))
    """Contract address of token that recipient will receive balance of"""
    sender = Column(String(42))
    """Ethereum address of transaction sender"""
    recipient = Column(String(42))
    """Ethereum address of transaction beneficiary (e.g. token transfer recipient)"""
    from_value = Column(NUMERIC())
    """Amount of source tokens spent"""
    to_value = Column(NUMERIC())
    """Amount of destination tokens received"""
    tx_index = Column(Integer())
    """Transaction index in the block the transaction was mined in, or None if not yet mined"""
    date_created = Column(DateTime, default=datetime.datetime.utcnow)
    """Datetime record was created"""
    date_updated = Column(DateTime, default=datetime.datetime.utcnow)
    """Datetime record was last updated"""
    date_checked = Column(DateTime, default=datetime.datetime.utcnow)
    """Datetime record was last checked for state change"""


    def __init__(self, tx_hash, sender, recipient, source_token_address, destination_token_address, from_value, to_value, block_number=None, tx_index=None, session=None):
        session = SessionBase.bind_session(session)
        q = session.query(Otx)
        q = q.filter(Otx.tx_hash==strip_0x(tx_hash))
        tx = q.first()
        if tx == None:
            SessionBase.release_session(session)
            raise NotLocalTxError('outgoing transaction record unknown {} (add a Tx first)'.format(tx_hash))
        self.otx_id = tx.id

        self.sender = sender
        self.recipient = recipient
        self.source_token_address = source_token_address
        self.destination_token_address = destination_token_address
        self.from_value = from_value
        self.to_value = to_value
        self.date_created = datetime.datetime.utcnow()
        self.date_updated = self.date_created
        self.date_checked = self.date_created
        if tx_index != None and block_number != tx.block:
            raise ValueError('Block number in argument {} does not match otx record {}'.format(block_number, tx.block))
        self.tx_index = tx_index

        SessionBase.release_session(session)


    def check(self):
        """Update the "checked" timestamp to current time.

        Only manipulates object, does not transaction or commit to backend.
        :todo: evaluate whether this should consume a session like other methods
        """
        self.date_checked = datetime.datetime.utcnow()


    @staticmethod
    def clone(
            tx_hash_original,
            tx_hash_new,
            session=None,
            ):
        """Copy tx cache data and associate it with a new transaction.

        :param tx_hash_original: tx cache data to copy
        :type tx_hash_original: str, 0x-hex
        :param tx_hash_new: tx hash to associate the copied entry with
        :type tx_hash_new: str, 0x-hex
        :param session: Sqlalchemy database session
        :type session: sqlalchemy.orm.Session
        :raise NotLocalTxError: Transaction does not exist in the local queue, or could not be created
        :raies TxStateChangeError: Attempt to clone an already confirmed transaction
        """
        session = SessionBase.bind_session(session)
        
        q = session.query(TxCache)
        q = q.join(Otx)
        q = q.filter(Otx.tx_hash==strip_0x(tx_hash_original))
        txc = q.first()

        if txc == None:
            SessionBase.release_session(session)
            raise NotLocalTxError('original {}'.format(tx_hash_original))
        if txc.tx_index != None:
            SessionBase.release_session(session)
            raise TxStateChangeError('cannot clone tx cache of confirmed tx {}'.format(tx_hash_original))

        session.flush()

        otx = Otx.load(tx_hash_new, session=session)

        if otx == None:
            SessionBase.release_session(session)
            raise NotLocalTxError('new {}'.format(tx_hash_new))

        txc_new = TxCache(
                otx.tx_hash,
                txc.sender,
                txc.recipient,
                txc.source_token_address,
                txc.destination_token_address,
                int(txc.from_value),
                int(txc.to_value),
                session=session,
                )
        session.add(txc_new)
        session.commit()

        SessionBase.release_session(session)


    # TODO: possible dead code
    @staticmethod
    def account(account_address, session=None):
        """Retrieves all transaction hashes for which the given Ethereum address is sender or recipient.

        :param account_address: Ethereum address to use in query.
        :type account_address: str, 0x-hex
        :param session: Sqlalchemy database session
        :type session: sqlalchemy.orm.Session
        :returns: Outgoing transactions
        :rtype: tuple, where first element is transaction hash
        """
        session = SessionBase.bind_session(session)

        q = session.query(Otx.tx_hash)
        q = q.join(TxCache)
        q = q.filter(or_(TxCache.sender==account_address, TxCache.recipient==account_address))
        txs = q.all()

        SessionBase.release_session(session)
        return list(txs)


    @staticmethod
    def set_final(tx_hash, block_number, tx_index, session=None):
        """Sets the transaction index for the confirmed transaction.

        The block number of the block that included the transaction must be set in the otx record before this method is called (see chainqueue.db.models.otx.Otx.minefail and chainqueue.db.models.otx.Otx.success). The block number in the record must match the block number given as argument. 

        :param tx_hash: Transaction hash, in hex
        :type tx_hash: str
        :param block_number: Block number transaction was included in
        :type block_number: int
        :param tx_index: The transaction index of the block to cache
        :type tx_index: int
        :param session: Sqlalchemy database session
        :type session: sqlalchemy.orm.Session
        :raises NotLocalTxError: Transaction does not exist in local queue, or block column is not set in otx record.
        """
        session = SessionBase.bind_session(session)

        q = session.query(TxCache)
        q = q.join(Otx)
        q = q.filter(Otx.tx_hash==strip_0x(tx_hash))
        q = q.filter(Otx.block==block_number)
        o = q.first()

        if o == None:
            raise NotLocalTxError(tx_hash, block_number)
                
        o.tx_index = tx_index
        session.add(o)
        session.flush()

        SessionBase.release_session(session)


    @staticmethod
    def load(tx_hash, session=None):
        """Retrieves the outgoing transaction record by transaction hash.

        :param tx_hash: Transaction hash
        :type tx_hash: str, 0x-hex
        :param session: Sqlalchemy database session
        :type session: sqlalchemy.orm.Session
        :rtype: chainqueue.db.models.tx.TxCache
        :returns: Transaction cache object
        """
        session = SessionBase.bind_session(session)
        
        q = session.query(TxCache)
        q = q.join(Otx)
        q = q.filter(Otx.tx_hash==strip_0x(tx_hash))

        SessionBase.release_session(session)

        return q.first()

