# standard imports
import os
import tempfile
import unittest
import logging

# external imports
from shep.store.file import SimpleFileStoreFactory
from chainlib.chain import ChainSpec

# local imports
from chainqueue import (
        Store,
        Status,
        )

# test imports
from tests.common import (
        MockCounter,
        MockTokenCache,
        MockCacheTokenTx,
        MockContentStore,
        )
from tests.base_shep import TestShepBase

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


class TestIntegrateBase(TestShepBase):

    def setUp(self):
        self.path = tempfile.mkdtemp()
        factory = SimpleFileStoreFactory(self.path).add
        self.state = Status(factory)
        content_store = MockContentStore()
        counter = MockCounter()
        chain_spec = ChainSpec('foo', 'bar', 42, 'baz')
        self.cache = MockTokenCache()
        self.store = Store(chain_spec, self.state, content_store, counter, cache=self.cache)


    def test_integration_valid(self):
        self.store.put(os.urandom(4).hex(), os.urandom(8).hex(), cache_adapter=MockCacheTokenTx)

    
    def test_state_default(self):
        hx = os.urandom(4).hex()
        self.store.put(hx, os.urandom(8).hex(), cache_adapter=MockCacheTokenTx)
        v = self.store.pending()
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0], hx)


    def test_state_enqueue(self):
        hx = os.urandom(4).hex()
        self.store.put(hx, os.urandom(8).hex(), cache_adapter=MockCacheTokenTx)
        self.store.get(hx)
        self.store.enqueue(hx)
        v = self.store.upcoming()
        self.assertEqual(len(v), 1)
        v = self.store.pending()
        self.assertEqual(len(v), 0)


    def test_state_defer(self):
        hx = os.urandom(4).hex()
        self.store.put(hx, os.urandom(8).hex(), cache_adapter=MockCacheTokenTx)
        self.store.fail(hx)
        v = self.store.deferred()
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0], hx)


    def test_state_multiple(self):
        hx = os.urandom(4).hex()
        self.store.put(hx, os.urandom(8).hex(), cache_adapter=MockCacheTokenTx)
        self.store.fail(hx)
        hx = os.urandom(8).hex()
        self.store.put(hx, os.urandom(8).hex(), cache_adapter=MockCacheTokenTx)
        self.store.fail(hx)
        v = self.store.deferred()
        self.assertEqual(len(v), 2)


    def test_state_multiple_sort(self):
        hx = os.urandom(4).hex()
        self.store.put(hx, os.urandom(8).hex(), cache_adapter=MockCacheTokenTx)
        self.store.fail(hx)
        hx = os.urandom(4).hex()
        self.store.put(hx, os.urandom(8).hex(), cache_adapter=MockCacheTokenTx)
        self.store.enqueue(hx)
        hx = os.urandom(4).hex()
        self.store.put(hx, os.urandom(8).hex(), cache_adapter=MockCacheTokenTx)
        self.store.fail(hx)
        hx = os.urandom(4).hex()
        self.store.put(hx, os.urandom(8).hex(), cache_adapter=MockCacheTokenTx)
        v = self.store.deferred()
        self.assertEqual(len(v), 2)


if __name__ == '__main__':
    unittest.main()
