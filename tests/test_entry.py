# standard imports
import os
import logging
import unittest

# external imports
from hexathon import add_0x
from chainlib.tx import Tx
from chainlib.block import Block

# local imports
from chainqueue import QueueEntry

# test imports
from tests.base_shep import TestShepBase
from tests.common import MockCacheTokenTx

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


class TestEntry(TestShepBase):
    
    def test_entry_get(self):
        signed_tx = add_0x(os.urandom(128).hex())
        nonce = 42
        entry = QueueEntry(self.store, cache_adapter=MockCacheTokenTx)
        tx_hash_one = entry.create(signed_tx)

        signed_tx = add_0x(os.urandom(128).hex())
        nonce = 42
        entry = QueueEntry(self.store, cache_adapter=MockCacheTokenTx)
        tx_hash_two = entry.create(signed_tx)

        txs = self.store.by_state()
        self.assertEqual(len(txs), 2)
     
        logg.debug('tx hash one {}'.format(tx_hash_one))
        entry = QueueEntry(self.store, tx_hash=tx_hash_one, cache_adapter=MockCacheTokenTx)
        entry.load()
        entry.sent()
        
        txs = self.store.by_state()
        self.assertEqual(len(txs), 1)

        txs = self.store.by_state(state=self.store.IN_NETWORK)
        self.assertEqual(len(txs), 1)

        entry.succeed(None, None)
        txs = self.store.by_state()
        self.assertEqual(len(txs), 1)
      
        entry = QueueEntry(self.store, tx_hash_two)
        entry.load()
        entry.sent()
        
        txs = self.store.by_state(state=self.store.IN_NETWORK)
        self.assertEqual(len(txs), 2)

        txs = self.store.by_state(state=self.store.IN_NETWORK, strict=True)
        self.assertEqual(len(txs), 1)


    def test_entry_change(self):
        signed_tx = add_0x(os.urandom(128).hex())
        nonce = 42
        entry = QueueEntry(self.store, cache_adapter=MockCacheTokenTx)
        tx_hash = entry.create(signed_tx)

        block = Block()
        block.number = 13
        tx = Tx(None)
        tx.index = 666

        entry.readysend()
        entry.reserve()
        entry.sendfail()

        entry = QueueEntry(self.store, tx_hash, cache_adapter=MockCacheTokenTx)
        entry.load()
        self.assertEqual(str(entry), tx_hash + ': SENDFAIL')
       

if __name__ == '__main__':
    unittest.main()
