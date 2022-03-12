# standard imports
import os
import logging
import unittest

# external imports
from hexathon import add_0x

# local imports
from chainqueue import QueueEntry

# test imports
from tests.base_shep import TestShepBase

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


class TestEntry(TestShepBase):
    
    def test_entry_get(self):
        tx_hash_one = add_0x(os.urandom(32).hex())
        signed_tx = add_0x(os.urandom(128).hex())
        nonce = 42
        entry = QueueEntry(self.store, tx_hash_one)
        entry.create(signed_tx)

        tx_hash_two = add_0x(os.urandom(32).hex())
        signed_tx = add_0x(os.urandom(128).hex())
        nonce = 42
        entry = QueueEntry(self.store, tx_hash_two)
        entry.create(signed_tx)

        txs = self.store.list()
        self.assertEqual(len(txs), 2)
      
        entry = QueueEntry(self.store, tx_hash_one)
        entry.load()
        entry.sent()
        
        txs = self.store.list()
        self.assertEqual(len(txs), 1)

        txs = self.store.list(state=self.store.IN_NETWORK)
        self.assertEqual(len(txs), 1)

        entry.succeed(0)
        txs = self.store.list()
        self.assertEqual(len(txs), 1)
      
        entry = QueueEntry(self.store, tx_hash_two)
        entry.load()
        entry.sent()
        
        txs = self.store.list(state=self.store.IN_NETWORK)
        self.assertEqual(len(txs), 2)

        txs = self.store.list(state=self.store.IN_NETWORK, strict=True)
        self.assertEqual(len(txs), 1)


if __name__ == '__main__':
    unittest.main()
