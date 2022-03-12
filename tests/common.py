# local imports
from chainqueue.cache import Cache


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
