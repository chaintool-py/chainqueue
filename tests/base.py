# standard imports
import logging
import unittest
import tempfile
import os
#import pysqlite

# external imports
from chainqueue.db.models.otx import Otx
from chainqueue.db.models.tx import TxCache
from chainlib.chain import ChainSpec
import alembic
import alembic.config
from hexathon import add_0x

# local imports
from chainqueue.db import dsn_from_config
from chainqueue.db.models.base import SessionBase
from chainqueue.tx import create

script_dir = os.path.realpath(os.path.dirname(__file__))

logging.basicConfig(level=logging.WARNING)
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
        SessionBase.connect(dsn, debug=True)

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


class TestOtxBase(TestBase):

    def setUp(self):
        super(TestOtxBase, self).setUp()
        self.tx_hash = add_0x(os.urandom(32).hex())
        self.tx = add_0x(os.urandom(128).hex())
        self.nonce = 42
        self.alice = add_0x(os.urandom(20).hex())

        tx_hash = create(self.nonce, self.alice, self.tx_hash, self.tx, self.chain_spec, session=self.session)
        self.assertEqual(tx_hash, self.tx_hash)


class TestTxBase(TestOtxBase):

    def setUp(self):
        super(TestTxBase, self).setUp()
        self.bob = add_0x(os.urandom(20).hex())
        self.foo_token = add_0x(os.urandom(20).hex())
        self.bar_token = add_0x(os.urandom(20).hex())
        self.from_value = 42
        self.to_value = 13

        txc = TxCache(
                self.tx_hash,
                self.alice,
                self.bob,
                self.foo_token,
                self.bar_token,
                self.from_value,
                self.to_value,
                session=self.session,
                )
        self.session.add(txc)
        self.session.commit()

        otx = Otx.load(self.tx_hash)
        self.assertEqual(txc.otx_id, otx.id)

