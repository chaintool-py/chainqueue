# standard imports
import datetime
import logging

# external imports
from sqlalchemy import Column, Enum, String, Integer, DateTime, Text, or_, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from hexathon import (
        strip_0x,
        )

# local imports
from .base import SessionBase
from .state import OtxStateLog
from chainqueue.db.enum import (
        StatusEnum,
        StatusBits,
        status_str,
        is_error_status,
        )
from chainqueue.error import TxStateChangeError

logg = logging.getLogger().getChild(__name__)


class Otx(SessionBase):
    """Outgoing transactions with local origin.

    :param nonce: Transaction nonce
    :type nonce: number
    :param address: Ethereum address of recipient - NOT IN USE, REMOVE
    :type address: str
    :param tx_hash: Tranasction hash 
    :type tx_hash: str, 0x-hex
    :param signed_tx: Signed raw transaction data
    :type signed_tx: str, 0x-hex
    """
    __tablename__ = 'otx'

    tracing = False
    """Whether to enable queue state tracing"""

    nonce = Column(Integer)
    date_created = Column(DateTime, default=datetime.datetime.utcnow)
    tx_hash = Column(String(66))
    signed_tx = Column(Text)
    status = Column(Integer)
    block = Column(Integer)


    def __set_status(self, status, session):
        self.status |= status
        session.add(self)
        session.flush()


    def __reset_status(self, status, session):
        status_edit = ~status & self.status
        self.status &= status_edit
        session.add(self)
        session.flush()
   

    def __status_already_set(self, status):
        r = bool(self.status & status)
        if r:
            logg.warning('status bit {} already set on {}'.format(status.name, self.tx_hash))
        return r


    def __status_not_set(self, status):
        r = not(self.status & status)
        if r:
            logg.warning('status bit {} not set on {}'.format(status.name, self.tx_hash))
        return r


    def set_block(self, block, session=None):
        """Set block number transaction was mined in.

        Only manipulates object, does not transaction or commit to backend.

        :param block: Block number
        :type block: number
        :raises cic_eth.db.error.TxStateChangeError: State change represents a sequence of events that should not exist.
        """
        session = SessionBase.bind_session(session)

        if self.block != None:
            SessionBase.release_session(session)
            raise TxStateChangeError('Attempted set block {} when block was already {}'.format(block, self.block))
        self.block = block
        session.add(self)
        session.flush()

        SessionBase.release_session(session)


    def waitforgas(self, session=None):
        """Marks transaction as suspended pending gas funding.

        Only manipulates object, does not transaction or commit to backend.

        :raises cic_eth.db.error.TxStateChangeError: State change represents a sequence of events that should not exist.
        """
        if self.__status_already_set(StatusBits.GAS_ISSUES):
            return

        session = SessionBase.bind_session(session)

        if self.status & StatusBits.FINAL:
            SessionBase.release_session(session)
            raise TxStateChangeError('GAS_ISSUES cannot be set on an entry with FINAL state set ({})'.format(status_str(self.status)))
        if self.status & StatusBits.IN_NETWORK:
            SessionBase.release_session(session)
            raise TxStateChangeError('GAS_ISSUES cannot be set on an entry with IN_NETWORK state set ({})'.format(status_str(self.status)))

        self.__set_status(StatusBits.GAS_ISSUES, session)
        self.__reset_status(StatusBits.QUEUED | StatusBits.DEFERRED, session)

        if self.tracing:
            self.__state_log(session=session)

        SessionBase.release_session(session)


    def fubar(self, session=None):
        """Marks transaction as "fubar." Any transaction marked this way is an anomaly and may be a symptom of a serious problem.

        Only manipulates object, does not transaction or commit to backend.
        """
        if self.__status_already_set(StatusBits.UNKNOWN_ERROR):
            return

        session = SessionBase.bind_session(session)

        if self.status & StatusBits.FINAL:
            SessionBase.release_session(session)
            raise TxStateChangeError('FUBAR cannot be set on an entry with FINAL state set ({})'.format(status_str(self.status)))
        if is_error_status(self.status):
            SessionBase.release_session(session)
            raise TxStateChangeError('FUBAR cannot be set on an entry with an error state already set ({})'.format(status_str(self.status)))
        if not self.status & StatusBits.RESERVED:
            SessionBase.release_session(session)
            raise TxStateChangeError('FUBAR on tx that has not been RESEREVED ({})'.format(status_str(self.status)))


        self.__set_status(StatusBits.UNKNOWN_ERROR | StatusBits.FINAL, session)
       
        if self.tracing:
            self.__state_log(session=session)

        SessionBase.release_session(session)


    def reject(self, session=None):
        """Marks transaction as "rejected," which means the node rejected sending the transaction to the network. The nonce has not been spent, and the transaction should be replaced.

        Only manipulates object, does not transaction or commit to backend.
        """
        if self.__status_already_set(StatusBits.NODE_ERROR):
            return

        session = SessionBase.bind_session(session)

        if self.status & StatusBits.FINAL:
            SessionBase.release_session(session)
            raise TxStateChangeError('REJECTED cannot be set on an entry with FINAL state set ({})'.format(status_str(self.status)))
        if self.status & StatusBits.IN_NETWORK:
            SessionBase.release_session(session)
            raise TxStateChangeError('REJECTED cannot be set on an entry already IN_NETWORK ({})'.format(status_str(self.status)))
        if is_error_status(self.status):
            SessionBase.release_session(session)
            raise TxStateChangeError('REJECTED cannot be set on an entry with an error state already set ({})'.format(status_str(self.status)))
        if not self.status & StatusBits.RESERVED:
            SessionBase.release_session(session)
            raise TxStateChangeError('REJECTED on tx that has not been RESEREVED ({})'.format(status_str(self.status)))



        self.__set_status(StatusBits.NODE_ERROR | StatusBits.FINAL, session)
            
        if self.tracing:
            self.__state_log(session=session)

        SessionBase.release_session(session)


    def override(self, manual=False, session=None):
        """Marks transaction as manually overridden.

        Only manipulates object, does not transaction or commit to backend.
        """

        session = SessionBase.bind_session(session)

        if self.status & StatusBits.FINAL:
            SessionBase.release_session(session)
            raise TxStateChangeError('OVERRIDDEN/OBSOLETED cannot be set on an entry with FINAL state set ({})'.format(status_str(self.status)))
        if self.status & StatusBits.IN_NETWORK:
            SessionBase.release_session(session)
            raise TxStateChangeError('OVERRIDDEN/OBSOLETED cannot be set on an entry already IN_NETWORK ({})'.format(status_str(self.status)))
        if self.status & StatusBits.OBSOLETE:
            SessionBase.release_session(session)
            raise TxStateChangeError('OVERRIDDEN/OBSOLETED cannot be set on an entry already OBSOLETE ({})'.format(status_str(self.status)))

        self.__set_status(StatusBits.OBSOLETE, session)
        #if manual:
        #    self.__set_status(StatusBits.MANUAL, session)
        self.__reset_status(StatusBits.QUEUED | StatusBits.IN_NETWORK, session)

        if self.tracing:
            self.__state_log(session=session)

        SessionBase.release_session(session)


    def manual(self, session=None):

        session = SessionBase.bind_session(session)


        if self.status & StatusBits.FINAL:
            SessionBase.release_session(session)
            raise TxStateChangeError('OVERRIDDEN/OBSOLETED cannot be set on an entry with FINAL state set ({})'.format(status_str(self.status)))

        self.__set_status(StatusBits.MANUAL, session)

        if self.tracing:
            self.__state_log(session=session)

        SessionBase.release_session(session)

    def retry(self, session=None):
        """Marks transaction as ready to retry after a timeout following a sendfail or a completed gas funding.

        Only manipulates object, does not transaction or commit to backend.

        :raises cic_eth.db.error.TxStateChangeError: State change represents a sequence of events that should not exist.
        """
        if self.__status_already_set(StatusBits.QUEUED):
            return

        session = SessionBase.bind_session(session)

        if self.status & StatusBits.FINAL:
            SessionBase.release_session(session)
            raise TxStateChangeError('RETRY cannot be set on an entry with FINAL state set ({})'.format(status_str(self.status)))
        if not is_error_status(self.status) and not StatusBits.IN_NETWORK & self.status > 0:
            SessionBase.release_session(session)
            raise TxStateChangeError('RETRY cannot be set on an entry that has no error ({})'.format(status_str(self.status)))

        self.__set_status(StatusBits.QUEUED, session)
        self.__reset_status(StatusBits.GAS_ISSUES, session)

        if self.tracing:
            self.__state_log(session=session)

        SessionBase.release_session(session)


    def readysend(self, session=None):
        """Marks transaction as ready for initial send attempt.

        Only manipulates object, does not transaction or commit to backend.

        :raises cic_eth.db.error.TxStateChangeError: State change represents a sequence of events that should not exist.
        """
        if self.__status_already_set(StatusBits.QUEUED):
            return

        session = SessionBase.bind_session(session)

        if self.status & StatusBits.FINAL:
            SessionBase.release_session(session)
            raise TxStateChangeError('READYSEND cannot be set on an entry with FINAL state set ({})'.format(status_str(self.status)))
        if is_error_status(self.status):
            SessionBase.release_session(session)
            raise TxStateChangeError('READYSEND cannot be set on an errored state ({})'.format(status_str(self.status)))

        self.__set_status(StatusBits.QUEUED, session)
        self.__reset_status(StatusBits.GAS_ISSUES, session)

        if self.tracing:
            self.__state_log(session=session)

        SessionBase.release_session(session)


    def sent(self, session=None):
        """Marks transaction as having been sent to network.

        Only manipulates object, does not transaction or commit to backend.

        :raises cic_eth.db.error.TxStateChangeError: State change represents a sequence of events that should not exist.
        """
        if self.__status_already_set(StatusBits.IN_NETWORK):
            return

        session = SessionBase.bind_session(session)

        if self.status & StatusBits.FINAL:
            SessionBase.release_session(session)
            raise TxStateChangeError('SENT cannot be set on an entry with FINAL state set ({})'.format(status_str(self.status)))

        if not self.status & StatusBits.RESERVED:
            SessionBase.release_session(session)
            raise TxStateChangeError('SENT on tx that has not been RESEREVED ({})'.format(status_str(self.status)))

        self.__set_status(StatusBits.IN_NETWORK, session)
        self.__reset_status(StatusBits.RESERVED | StatusBits.DEFERRED | StatusBits.QUEUED | StatusBits.LOCAL_ERROR | StatusBits.NODE_ERROR, session)

        if self.tracing:
            self.__state_log(session=session)

        SessionBase.release_session(session)


    def sendfail(self, session=None):
        """Marks that an attempt to send the transaction to the network has failed.

        Only manipulates object, does not transaction or commit to backend.

        :raises cic_eth.db.error.TxStateChangeError: State change represents a sequence of events that should not exist.
        """
        if self.__status_already_set(StatusBits.NODE_ERROR):
            return

        session = SessionBase.bind_session(session)

        if self.status & StatusBits.FINAL:
            SessionBase.release_session(session)
            raise TxStateChangeError('SENDFAIL cannot be set on an entry with FINAL state set ({})'.format(status_str(self.status)))
        if self.status & StatusBits.IN_NETWORK:
            SessionBase.release_session(session)
            raise TxStateChangeError('SENDFAIL cannot be set on an entry with IN_NETWORK state set ({})'.format(status_str(self.status)))
        if not self.status & StatusBits.RESERVED:
            SessionBase.release_session(session)
            raise TxStateChangeError('SENDFAIL on tx that has not been RESEREVED ({})'.format(status_str(self.status)))

        self.__set_status(StatusBits.LOCAL_ERROR | StatusBits.DEFERRED, session)
        self.__reset_status(StatusBits.RESERVED | StatusBits.QUEUED | StatusBits.GAS_ISSUES, session)

        if self.tracing:
            self.__state_log(session=session)

        SessionBase.release_session(session)


    def reserve(self, session=None):
        """Marks that a process to execute send attempt is underway

        Only manipulates object, does not transaction or commit to backend.

        :raises cic_eth.db.error.TxStateChangeError: State change represents a sequence of events that should not exist.
        """
        if self.__status_already_set(StatusBits.RESERVED):
            return

        session = SessionBase.bind_session(session)

        if self.status & StatusBits.QUEUED == 0:
            SessionBase.release_session(session)
            raise TxStateChangeError('RESERVED cannot be set on an entry without QUEUED state set ({})'.format(status_str(self.status)))
        if self.status & StatusBits.FINAL:
            SessionBase.release_session(session)
            raise TxStateChangeError('RESERVED cannot be set on an entry with FINAL state set ({})'.format(status_str(self.status)))
        if self.status & StatusBits.IN_NETWORK:
            SessionBase.release_session(session)
            raise TxStateChangeError('RESERVED cannot be set on an entry with IN_NETWORK state set ({})'.format(status_str(self.status)))

        self.__reset_status(StatusBits.QUEUED, session)
        self.__set_status(StatusBits.RESERVED, session)

        if self.tracing:
            self.__state_log(session=session)

        SessionBase.release_session(session)



    def minefail(self, block, session=None):
        """Marks that transaction was mined but code execution did not succeed.

        Only manipulates object, does not transaction or commit to backend.

        :param block: Block number transaction was mined in.
        :type block: number
        :raises cic_eth.db.error.TxStateChangeError: State change represents a sequence of events that should not exist.
        """
        if self.__status_already_set(StatusBits.NETWORK_ERROR):
            return

        session = SessionBase.bind_session(session)

        if self.status & StatusBits.FINAL:
            SessionBase.release_session(session)
            raise TxStateChangeError('REVERTED cannot be set on an entry with FINAL state set ({})'.format(status_str(self.status)))
        if not self.status & StatusBits.IN_NETWORK:
            SessionBase.release_session(session)
            raise TxStateChangeError('REVERTED cannot be set on an entry without IN_NETWORK state set ({})'.format(status_str(self.status)))

        if block != None:
            self.block = block

        self.__set_status(StatusBits.NETWORK_ERROR | StatusBits.FINAL, session)

        if self.tracing:
            self.__state_log(session=session)

        SessionBase.release_session(session)


    def cancel(self, confirmed=False, session=None):
        """Marks that the transaction has been succeeded by a new transaction with same nonce.

        If set to confirmed, the previous state must be OBSOLETED, and will transition to CANCELLED - a finalized state. Otherwise, the state must follow a non-finalized state, and will be set to OBSOLETED.

        Only manipulates object, does not transaction or commit to backend.

        :param confirmed: Whether transition is to a final state.
        :type confirmed: bool
        :raises cic_eth.db.error.TxStateChangeError: State change represents a sequence of events that should not exist.
        """
        session = SessionBase.bind_session(session)

        if self.status & StatusBits.FINAL:
            SessionBase.release_session(session)
            raise TxStateChangeError('CANCEL cannot be set on an entry with FINAL state set ({})'.format(status_str(self.status)))

        if confirmed:
            if self.status > 0 and not self.status & StatusBits.OBSOLETE:
                SessionBase.release_session(session)
                raise TxStateChangeError('CANCEL can only be set on an entry marked OBSOLETE ({})'.format(status_str(self.status)))
            self.__set_status(StatusEnum.CANCELLED, session)
        else:
            self.__set_status(StatusEnum.OBSOLETED, session)

        if self.tracing:
            self.__state_log(session=session)

        SessionBase.release_session(session)


    def success(self, block, session=None):
        """Marks that transaction was successfully mined.

        Only manipulates object, does not transaction or commit to backend.

        :param block: Block number transaction was mined in.
        :type block: number
        :raises cic_eth.db.error.TxStateChangeError: State change represents a sequence of events that should not exist.
        """

        session = SessionBase.bind_session(session)

        if self.status & StatusBits.FINAL:
            SessionBase.release_session(session)
            raise TxStateChangeError('SUCCESS cannot be set on an entry with FINAL state set ({})'.format(status_str(self.status)))
        if not self.status & StatusBits.IN_NETWORK:
            SessionBase.release_session(session)
            raise TxStateChangeError('SUCCESS cannot be set on an entry without IN_NETWORK state set ({})'.format(status_str(self.status)))
        if is_error_status(self.status):
            SessionBase.release_session(session)
            raise TxStateChangeError('SUCCESS cannot be set on an entry with error state set ({})'.format(status_str(self.status)))

        if block != None:
            self.block = block
        self.__set_status(StatusEnum.SUCCESS, session)

        if self.tracing:
            self.__state_log(session=session)

        SessionBase.release_session(session)


    @staticmethod
    def get(status=0, limit=4096, status_exact=True, session=None):
        """Returns outgoing transaction lists by status.

        Status may either be matched exactly, or be an upper bound of the integer value of the status enum.

        :param status: Status value to use in query
        :type status: cic_eth.db.enum.StatusEnum
        :param limit: Max results to return
        :type limit: number
        :param status_exact: Whether or not to perform exact status match
        :type bool:
        :returns: List of transaction hashes
        :rtype: tuple, where first element is transaction hash
        """
        e = None

        session = SessionBase.bind_session(session)

        if status_exact:
            e = session.query(Otx.tx_hash).filter(Otx.status==status).order_by(Otx.date_created.asc()).limit(limit).all()
        else:
            e = session.query(Otx.tx_hash).filter(Otx.status<=status).order_by(Otx.date_created.asc()).limit(limit).all()
        
        SessionBase.release_session(session)
        return e


    @staticmethod
    def load(tx_hash, session=None):
        """Retrieves the outgoing transaction record by transaction hash.

        :param tx_hash: Transaction hash
        :type tx_hash: str, 0x-hex
        """
        session = SessionBase.bind_session(session)
        
        q = session.query(Otx)
        q = q.filter(Otx.tx_hash==strip_0x(tx_hash))

        SessionBase.release_session(session)

        return q.first()


    

    def __state_log(self, session):
        l = OtxStateLog(self)
        session.add(l)


    # TODO: it is not safe to return otx here unless session has been passed in
    @staticmethod
    def add(nonce, tx_hash, signed_tx, session=None):
        external_session = session != None

        session = SessionBase.bind_session(session)

        otx = Otx(nonce, tx_hash, signed_tx)
        session.add(otx)
        session.flush()
        if otx.tracing:
            otx.__state_log(session=session)
        session.flush()

        SessionBase.release_session(session)
        
        if not external_session:
            return None

        return otx


    def __init__(self, nonce, tx_hash, signed_tx):
        self.nonce = nonce
        self.tx_hash = strip_0x(tx_hash)
        self.signed_tx = strip_0x(signed_tx)
        self.status = StatusEnum.PENDING
