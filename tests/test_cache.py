# standard imports
import os
import logging
import unittest
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
from tests.common import (
        MockTokenCache,
        MockCacheTokenTx,
        )

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


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
        self.assertEqual(tx.hash[:11], 'ashbashhash')


    def test_cache_putget(self):
        a = b'foo'
        tx = MockCacheTokenTx()
        tx.deserialize(a)
        self.cache.put(self.chain_spec, tx)
        tx_retrieved = self.cache.get(self.chain_spec, tx.hash)
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
