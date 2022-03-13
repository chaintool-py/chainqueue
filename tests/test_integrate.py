# standard imports
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
        self.store.put(b'foo'.hex(), b'bar'.hex(), cache_adapter=MockCacheTokenTx)


    def test_state_enqueu(self):
        hx = b'foo'.hex()
        self.store.put(hx, b'bar'.hex(), cache_adapter=MockCacheTokenTx)
        self.store.get(hx)
        self.store.enqueue(hx)
        v = self.store.upcoming()
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0], hx)


    def test_state_defer(self):
        hx = b'foo'.hex()
        self.store.put(hx, b'bar'.hex(), cache_adapter=MockCacheTokenTx)
        self.store.get(hx)
        self.store.fail(hx)


if __name__ == '__main__':
    unittest.main()
