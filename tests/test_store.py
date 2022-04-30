# standard imports
import os
import tempfile
import unittest
import logging
import shutil

# external imports
from chainlib.chain import ChainSpec
from shep.store.noop import NoopStoreFactory

# local imports
from chainqueue.store.fs import (
        IndexStore,
        CounterStore,
        )
from chainqueue.store.base import Store
from chainqueue.error import DuplicateTxError
from chainqueue.state import Status

# tests imports
from tests.common import (
        MockTokenCache,
        MockCacheTokenTx,
        )

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()

class TestStoreImplementations(unittest.TestCase):

    def setUp(self):
        self.path = tempfile.mkdtemp()
      

    def tearDown(self):
        shutil.rmtree(self.path)

    
    def test_basic_index(self):
        store = IndexStore(self.path)
        hx = os.urandom(32).hex()
        data = 'foo_bar_baz'
        store.put(hx, data)
        r = store.get(hx)
        self.assertEqual(data, r)


    def test_basic_counter(self):
        store = CounterStore(self.path)
        v = store.next()
        self.assertEqual(v, 0)
        v = store.next()
        self.assertEqual(v, 1)

        store = CounterStore(self.path)
        v = store.next()
        self.assertEqual(v, 2)


    def test_duplicate(self):
        store = IndexStore(self.path)
        hx = os.urandom(32).hex()
        data = 'foo_bar_baz'
        store.put(hx, data)
        with self.assertRaises(DuplicateTxError):
            store.put(hx, data)


    def test_upcoming_limit(self):
        index_store = IndexStore(self.path)
        counter_store = CounterStore(self.path)
        chain_spec = ChainSpec('foo', 'bar', 42, 'baz') 
        factory = NoopStoreFactory().add
        state_store = Status(factory)
        cache_store = MockTokenCache()
        queue_store = Store(chain_spec, state_store, index_store, counter_store, cache=cache_store)

        txs = []
        for i in range(3):
            tx_src = os.urandom(128).hex()
            tx = queue_store.put(tx_src, cache_adapter=MockCacheTokenTx)
            txs.append(tx)

        r = queue_store.upcoming(limit=3)
        self.assertEqual(len(r), 0)

        for tx in txs:
            queue_store.enqueue(tx[1])

        r = queue_store.upcoming(limit=3)
        self.assertEqual(len(r), 3)

        queue_store.send_start(txs[0][1])
        r = queue_store.upcoming(limit=3)
        self.assertEqual(len(r), 2)

        queue_store.send_end(txs[0][1])
        r = queue_store.upcoming(limit=3)
        self.assertEqual(len(r), 2)


if __name__ == '__main__':
    unittest.main()
