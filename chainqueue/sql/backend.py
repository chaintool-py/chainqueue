# local imports
from chainqueue.sql.tx import create
from chainqueue.db.models.base import SessionBase


class SQLBackend:

    def __init__(self, conn_spec, *args, **kwargs):
        SessionBase.connect(conn_spec, pool_size=kwargs.get('poolsize', 0), debug=kwargs.get('debug', False))
        self.create = create


    def create_session(self):
        return SessionBase.create_session()
