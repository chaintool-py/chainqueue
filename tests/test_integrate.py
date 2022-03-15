# standard imports
import os
import tempfile
import unittest
import logging
import time

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
        self.store.put(os.urandom(8).hex(), cache_adapter=MockCacheTokenTx)

    
    def test_state_default(self):
        (s, hx) = self.store.put(os.urandom(8).hex(), cache_adapter=MockCacheTokenTx)
        v = self.store.pending()
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0], hx)


    def test_state_enqueue(self):
        (s, hx) = self.store.put(os.urandom(8).hex(), cache_adapter=MockCacheTokenTx)
        self.store.get(hx)
        self.store.enqueue(hx)
        v = self.store.upcoming()
        self.assertEqual(len(v), 1)
        v = self.store.pending()
        self.assertEqual(len(v), 0)


    def test_state_defer(self):
        (s, hx) = self.store.put(os.urandom(8).hex(), cache_adapter=MockCacheTokenTx)
        self.store.reserve(hx)
        self.store.fail(hx)
        v = self.store.deferred()
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0], hx)


    def test_state_multiple(self):
        (s, hx) = self.store.put(os.urandom(8).hex(), cache_adapter=MockCacheTokenTx)
        self.store.reserve(hx)
        self.store.fail(hx)
      
        (s, hx) = self.store.put(os.urandom(8).hex(), cache_adapter=MockCacheTokenTx)
        self.store.reserve(hx)
        self.store.fail(hx)
        v = self.store.deferred()
        self.assertEqual(len(v), 2)


    def test_state_multiple_sort(self):
        (s, hx) = self.store.put(os.urandom(8).hex(), cache_adapter=MockCacheTokenTx)
        self.store.reserve(hx)
        self.store.fail(hx)
       
        (s, hx) = self.store.put(os.urandom(8).hex(), cache_adapter=MockCacheTokenTx)
        self.store.enqueue(hx)
        
        (s, hx) = self.store.put(os.urandom(8).hex(), cache_adapter=MockCacheTokenTx)
        self.store.reserve(hx)
        self.store.fail(hx)

        self.store.put(os.urandom(8).hex(), cache_adapter=MockCacheTokenTx)
        v = self.store.deferred()
        self.assertEqual(len(v), 2)


    def test_state_date_threshold(self):
        (s, hx) = self.store.put(os.urandom(8).hex(), cache_adapter=MockCacheTokenTx)
        self.store.reserve(hx)
        self.store.fail(hx)
        then = self.store.modified(s)
        time.sleep(0.1)

        (s, hx) = self.store.put(os.urandom(8).hex(), cache_adapter=MockCacheTokenTx)
        self.store.reserve(hx)
        self.store.fail(hx)

        v = self.store.deferred(threshold=then)
        self.assertEqual(len(v), 1)


if __name__ == '__main__':
    unittest.main()
