# standard imports
import os
import logging
import unittest
import tempfile

# external imports
from hexathon import add_0x
from shep.store.file import SimpleFileStoreFactory
from shep.error import StateTransitionInvalid

# local imports
from chainqueue import Status
from chainqueue.tx import Tx

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


class TestShepBase(unittest.TestCase):

    def setUp(self):
        self.path = tempfile.mkdtemp()
        factory = SimpleFileStoreFactory(self.path).add
        self.state = Status(factory)


class TestShep(TestShepBase):
   
    def test_shep_setup(self):
        pass


    def test_shep_tx(self):
        tx_hash = add_0x(os.urandom(20).hex())
        signed_tx = add_0x(os.urandom(128).hex())
        nonce = 42
        tx = Tx(self.state, nonce, tx_hash, signed_tx)
        tx.create()
        logg.debug('file {}'.format(self.path))


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
