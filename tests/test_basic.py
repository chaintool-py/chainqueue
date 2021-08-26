# standard imports
import os
import logging
import unittest

# external imports
from hexathon import (
        strip_0x,
        add_0x,
        )

# local imports
from chainqueue.db.models.otx import Otx
from chainqueue.db.models.tx import TxCache

# test imports
from tests.chainqueue_base import TestBase

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()

class TestBasic(TestBase):

    def test_hello(self):
        pass


    def test_otx(self):
        tx_hash = add_0x(os.urandom(32).hex())
        address = add_0x(os.urandom(20).hex())
        tx = add_0x(os.urandom(128).hex())
        nonce = 42
        otx = Otx(nonce, tx_hash, tx)
        self.session.add(otx)


    def test_tx(self):
        tx_hash = add_0x(os.urandom(32).hex())
        tx = add_0x(os.urandom(128).hex())
        nonce = 42
        otx = Otx(nonce, tx_hash, tx)
        self.session.add(otx)

        alice = add_0x(os.urandom(20).hex())
        bob = add_0x(os.urandom(20).hex())
        foo_token = add_0x(os.urandom(20).hex())
        bar_token = add_0x(os.urandom(20).hex())
        from_value = 13
        to_value = 666

        block_number = 1024
        tx_index = 1337

        txc = TxCache(
            tx_hash,
            alice,
            bob,
            foo_token,
            bar_token,
            from_value,
            to_value,
            block_number=block_number,
            tx_index=tx_index,
            session=self.session,
                )
        self.session.add(txc)

if __name__ == '__main__':
    unittest.main()
