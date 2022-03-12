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


class MockContentStore:

    def __init__(self):
        self.store = {}


    def put(self, k, v):
        self.store[k] = v


    def get(self, k):
        return self.store.get(k)


class MockCounter:

    def __init__(self):
        self.c = 0


    def next(self):
        c = self.c
        self.c += 1
        return c


class TestShepBase(unittest.TestCase):

    def setUp(self):
        self.path = tempfile.mkdtemp()
        factory = SimpleFileStoreFactory(self.path).add
        self.state = Status(factory)
        content_store = MockContentStore()
        counter = MockCounter()
        self.store = Store(self.state, content_store, counter)
