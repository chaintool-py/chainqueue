# standard imports
import hashlib

# local imports
from chainqueue.cache import (
        Cache,
        CacheTokenTx,
        )


class MockCounter:

    def __init__(self):
        self.c = 0


    def next(self):
        c = self.c
        self.c += 1
        return c


class MockTokenCache(Cache):

    def __init__(self):
        self.db = {}
        self.last_filter = None

    def put(self, chain_spec, cache_tx):
        self.db[cache_tx.tx_hash] = cache_tx


    def get(self, chain_spec, tx_hash):
        return self.db[tx_hash]


    def by_nonce(self, cache_filter):
        self.last_filter = cache_filter


    def by_date(self, cache_filter=None):
        self.last_filter = cache_filter


    def count(self, cache_filter): 
        self.last_filter = cache_filter


class MockCacheTokenTx(CacheTokenTx):

    def deserialize(self, signed_tx):
        h = hashlib.sha1()
        try:
            h.update(signed_tx + b'\x01')
        except TypeError:
            h.update(signed_tx.encode('utf-8') + b'\x01')
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

        self.init(tx_hash, nonce, sender, recipient, value)
        self.set('src_token', token)
        self.set('dst_token', token)
        self.set('src_value', token_value)
        self.set('dst_value', token_value)
        self.confirm(42, 13, 1024000)

        return self


class MockContentStore:

    def __init__(self):
        self.store = {}


    def put(self, k, v):
        self.store[k] = v


    def get(self, k):
        return self.store.get(k)
