# standard imports
import datetime

# external imports
from sqlalchemy import Column, Integer, DateTime, ForeignKey

# local imports
from .base import SessionBase


class OtxStateLog(SessionBase):
    """Records state change history for a transaction.

    :param otx: Otx object to read and record state for
    :type otx: chainqueue.db.models.otx.
    """
    __tablename__ = 'otx_state_log'

    date = Column(DateTime, default=datetime.datetime.utcnow)
    """Date for log entry"""
    status = Column(Integer)
    """Status value after change"""
    otx_id = Column(Integer, ForeignKey('otx.id'))
    """Foreign key of otx record"""

    def __init__(self, otx):
        self.otx_id = otx.id
        self.status = otx.status
        self.date = datetime.datetime.utcnow()
