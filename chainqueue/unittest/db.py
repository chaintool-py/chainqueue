# standard imports
import logging
import os

# external imports
import alembic
import alembic.config

# local imports
from chainqueue.db.models.base import SessionBase
from chainqueue.db import dsn_from_config

logg = logging.getLogger(__name__)


db_config = {
    'DATABASE_ENGINE': 'sqlite',
    'DATABASE_DRIVER': 'pysqlite',
    'DATABASE_NAME': 'chainqueue.sqlite',
        }


class ChainQueueDb:

    base = SessionBase

    def __init__(self, debug=False):
        logg.debug('config {}'.format(db_config))
        self.dsn = dsn_from_config(db_config)

        self.base.poolable = False
        self.base.transactional = False
        self.base.procedural = False
        self.base.connect(self.dsn, debug=debug) # TODO: evaluates to "true" even if string is 0

        rootdir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..')
        dbdir = os.path.join(rootdir, 'chainqueue', 'db')
        #migrationsdir = os.path.join(dbdir, 'migrations', db_config.get('DATABASE_ENGINE'))
        migrationsdir = os.path.join(dbdir, 'migrations', 'default')
        logg.info('using migrations directory {}'.format(migrationsdir))

        ac = alembic.config.Config(os.path.join(migrationsdir, 'alembic.ini'))
        ac.set_main_option('sqlalchemy.url', self.dsn)
        ac.set_main_option('script_location', migrationsdir)

        alembic.command.downgrade(ac, 'base')
        alembic.command.upgrade(ac, 'head')


    def bind_session(self, session=None):
        return self.base.bind_session(session)

    
    def release_session(self, session=None):
        return self.base.release_session(session)
