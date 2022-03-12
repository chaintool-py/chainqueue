# standard imports
import os
import logging
import unittest
import hashlib

# external imports
from hexathon import add_0x

# local imports
from chainqueue import QueueEntry
from chainqueue.cache import (
        CacheTokenTx,
        )

# test imports
from tests.base_shep import TestShepBase

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


class MockCacheTokenTx(CacheTokenTx):

    def deserialize(self, signed_tx):
        h = hashlib.sha1()
        h.update(signed_tx + b'\x01')
        z = h.digest()
        nonce = int.from_bytes(z[:4], 'big')
        token_value = int.from_bytes(z[4:8], 'big')
        value = int.from_bytes(z[8:12], 'big')
        
        h = hashlib.sha1()
        h.update(z)
        z = h.digest()
        sender = z.hex()

        h = hashlib.sha1()
        h.update(z)
        z = h.digest()
        recipient = z.hex()

        h = hashlib.sha1()
        h.update(z)
        z = h.digest()
        token = z.hex()

        tx = CacheTokenTx()
        tx.init(nonce, sender, recipient, value)
        tx.set('src_token', token)
        tx.set('dst_token', token)
        tx.set('src_value', token_value)
        tx.set('dst_value', token_value)

        return tx


class TestCache(TestShepBase):

    def setUp(self):
        super(TestCache, self).setUp()
        self.tx = MockCacheTokenTx()

    def test_basic_translator(self):
        a = b'foo'
        tx = self.tx.deserialize(a)
        print(tx)


if __name__ == '__main__':
    unittest.main()
