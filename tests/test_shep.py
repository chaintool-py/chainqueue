# standard imports
import os
import logging
import unittest

# external imports
from hexathon import (
        add_0x,
        strip_0x,
        )
from shep.error import StateTransitionInvalid

# local imports
from chainqueue import QueueEntry

# test imports
from tests.base_shep import TestShepBase

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


class TestShep(TestShepBase):
   
    def test_shep_setup(self):
        pass


    def test_shep_tx(self):
        tx_hash = add_0x(os.urandom(20).hex())
        signed_tx = add_0x(os.urandom(128).hex())
        nonce = 42
        tx = QueueEntry(self.store, tx_hash)
        tx.create(nonce, signed_tx)

        tx_retrieved = QueueEntry(self.store, tx_hash)
        tx_retrieved.load()
        self.assertEqual(tx_retrieved.signed_tx, strip_0x(signed_tx))


    def test_shep_valid(self):
        self.state.put('foo', 'bar')
        self.state.set('foo', self.state.IN_NETWORK)
        self.state.set('foo', self.state.FINAL)
    

    def test_shep_invalid(self):
        self.state.put('foo', 'bar')
        self.state.set('foo', self.state.FINAL)
        with self.assertRaises(StateTransitionInvalid):
            self.state.move('foo', self.state.INSUFFICIENT_FUNDS)
    

if __name__ == '__main__':
    unittest.main()
