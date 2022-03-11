# standard imports
import tempfile
import unittest

# external imports
from shep.store.file import SimpleFileStoreFactory

# local imports
from chainqueue import (
        Store,
        Status,
        )


class MockIndexStore:

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
        self.store = Store(self.state, MockIndexStore())
