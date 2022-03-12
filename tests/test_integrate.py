# standard imports
import tempfile
import unittest

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
        MockTokenCache
        )


class MockContentStore:

    def __init__(self):
        self.store = {}


    def put(self, k, v):
        self.store[k] = v


    def get(self, k):
        return self.store.get(k)


class TestShepBase(unittest.TestCase):

    def setUp(self):
        self.path = tempfile.mkdtemp()
        factory = SimpleFileStoreFactory(self.path).add
        self.state = Status(factory)
        content_store = MockContentStore()
        counter = MockCounter()
        chain_spec = ChainSpec('foo', 'bar', 42, 'baz')
        self.cache = MockTokenCache()
        self.store = Store(chain_spec, self.state, content_store, counter, cache=self.cache)


    def test_basic(self):
        pass


if __name__ == '__main__':
    unittest.main()
