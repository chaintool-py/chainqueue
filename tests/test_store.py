# standard imports
import os
import tempfile
import unittest
import logging
import shutil

# external imports

# local imports
from chainqueue.store.fs import (
        IndexStore,
        CounterStore,
        )
from chainqueue.error import DuplicateTxError


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


if __name__ == '__main__':
    unittest.main()
