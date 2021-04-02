# standard imports
import logging
import unittest
import tempfile
import os
#import pysqlite

# external imports
from chainlib.chain import ChainSpec
import alembic
import alembic.config

# local imports
from chainqueue.db import dsn_from_config
from chainqueue.db.models.base import SessionBase

script_dir = os.path.realpath(os.path.dirname(__file__))

logg = logging.getLogger().getChild(__name__)


class TestBase(unittest.TestCase):

    def setUp(self):
        rootdir = os.path.dirname(os.path.dirname(__file__))
        dbdir = os.path.join(rootdir, 'chainqueue', 'db')
        #migrationsdir = os.path.join(dbdir, 'migrations', load_config.get('DATABASE_ENGINE'))
        #if not os.path.isdir(migrationsdir):
        migrationsdir = os.path.join(dbdir, 'migrations', 'default')
        logg.info('using migrations directory {}'.format(migrationsdir))

        config = {
            'DATABASE_ENGINE': 'sqlite',
            'DATABASE_DRIVER': 'pysqlite',
            'DATABASE_NAME': 'chainqueue.sqlite',
                }
        logg.debug('config {}'.format(config))

        dsn = dsn_from_config(config)
        SessionBase.poolable = False
        SessionBase.transactional = False
        SessionBase.procedural = False
        SessionBase.connect(dsn, debug=False)

        ac = alembic.config.Config(os.path.join(migrationsdir, 'alembic.ini'))
        ac.set_main_option('sqlalchemy.url', dsn)
        ac.set_main_option('script_location', migrationsdir)

        alembic.command.downgrade(ac, 'base')
        alembic.command.upgrade(ac, 'head')

        self.session = SessionBase.create_session()

        self.chain_spec = ChainSpec('evm', 'foo', 42, 'bar')


    def tearDown(self):
        self.session.commit()
        self.session.close()
