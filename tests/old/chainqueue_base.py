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
from hexathon import (
        add_0x,
        strip_0x,
        )

# local imports
from chainqueue.sql.tx import create
from chainqueue.unittest.db import ChainQueueDb
from chainqueue.sql.backend import SQLBackend

script_dir = os.path.realpath(os.path.dirname(__file__))

logg = logging.getLogger(__name__)


class TestBase(unittest.TestCase):

    def setUp(self):
        debug = bool(os.environ.get('DATABASE_DEBUG', False))
        self.db = ChainQueueDb(debug=debug)
        self.session = self.db.bind_session()
        self.chain_spec = ChainSpec('evm', 'foo', 42, 'bar')
    

    def tearDown(self):
        self.session.commit()
        self.db.release_session(self.session)


class TestOtxBase(TestBase):

    def setUp(self):
        super(TestOtxBase, self).setUp()
        self.tx_hash = os.urandom(32).hex()
        self.tx = os.urandom(128).hex()
        self.nonce = 42
        self.alice = add_0x(os.urandom(20).hex())

        tx_hash = create(self.chain_spec, self.nonce, self.alice, self.tx_hash, self.tx, session=self.session)
        self.assertEqual(tx_hash, self.tx_hash)
        self.session.commit()

        logg.info('using tx hash {}'.format(self.tx_hash))


class TestTxBase(TestOtxBase):

    def setUp(self):
        super(TestTxBase, self).setUp()
        self.bob = add_0x(os.urandom(20).hex())
        self.carol = add_0x(os.urandom(20).hex())
        self.foo_token = add_0x(os.urandom(20).hex())
        self.bar_token = add_0x(os.urandom(20).hex())
        self.from_value = 42
        self.to_value = 13

        backend = SQLBackend(self.db.dsn)
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
        txc = TxCache.load(self.tx_hash)

        self.assertEqual(txc.otx_id, otx.id)

