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

# test imports
from tests.base import TestBase

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


if __name__ == '__main__':
    unittest.main()
