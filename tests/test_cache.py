# standard imports
import os
import logging
import unittest
import hashlib
import math

# external imports
from hexathon import add_0x
from chainlib.chain import ChainSpec

# local imports
from chainqueue import QueueEntry
from chainqueue.cache import (
        CacheTokenTx,
        CacheFilter,
        )

# test imports
from tests.base_shep import TestShepBase
from tests.common import MockTokenCache

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

        h = hashlib.sha256()
        h.update(z)
        z = h.digest()
        tx_hash = z.hex()

        #tx = CacheTokenTx(normalizer=self.normalizer)
        self.init(tx_hash, nonce, sender, recipient, value)
        self.set('src_token', token)
        self.set('dst_token', token)
        self.set('src_value', token_value)
        self.set('dst_value', token_value)
        self.confirm(42, 13, 1024000)

        return self


class MockNormalizer:

    def address(self, v):
        return 'address' + v


    def value(self, v):
        dv = int(math.log10(v) + 1)
        return float(v / (10 ** dv))


    def hash(self, v):
        return 'ashbashhash' + v


class TestCache(TestShepBase):

    def setUp(self):
        super(TestCache, self).setUp()
        self.chain_spec = ChainSpec('foo', 'bar', 42, 'baz')
        self.cache = MockTokenCache()

    
    def test_cache_instance(self):
        normalizer = MockNormalizer()
        a = b'foo'
        tx = MockCacheTokenTx(normalizer=normalizer)
        tx.deserialize(a)
        self.assertTrue(isinstance(tx.value, float))
        self.assertEqual(tx.sender[:4], 'addr')
        self.assertEqual(tx.recipient[:4], 'addr')
        self.assertEqual(tx.tx_hash[:11], 'ashbashhash')


    def test_cache_putget(self):
        a = b'foo'
        tx = MockCacheTokenTx()
        tx.deserialize(a)
        self.cache.put(self.chain_spec, tx)
        tx_retrieved = self.cache.get(self.chain_spec, tx.tx_hash)
        self.assertEqual(tx, tx_retrieved)


    def test_cache_filter(self):
        normalizer = MockNormalizer()
        fltr = CacheFilter(normalizer=normalizer)

        sender = os.urandom(20).hex()
        fltr.add_senders(sender)

        recipient_one = os.urandom(20).hex()
        recipient_two = os.urandom(20).hex()
        fltr.add_recipients([recipient_one, recipient_two])

        self.assertEqual(fltr.senders[0][:4], 'addr')
        self.assertEqual(fltr.recipients[1][:4], 'addr')


    def test_cache_query(self):
        a = os.urandom(20).hex()
        fltr = CacheFilter(nonce=42)
        self.cache.count(fltr)
        self.assertEqual(self.cache.last_filter, fltr)


if __name__ == '__main__':
    unittest.main()
