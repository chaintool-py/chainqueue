# standard imports
import datetime

# external imports
from sqlalchemy import Column, Integer, DateTime, ForeignKey

# local imports
from .base import SessionBase


class OtxStateLog(SessionBase):

    __tablename__ = 'otx_state_log'

    date = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(Integer)
    otx_id = Column(Integer, ForeignKey('otx.id'))


    def __init__(self, otx):
        self.otx_id = otx.id
        self.status = otx.status


