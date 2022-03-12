# standard imports
import logging
import re
import datetime

# local imports
from chainqueue.cache import CacheTx


logg = logging.getLogger(__name__)


def to_key(t, n, k):
    return '{}_{}_{}'.format(t, n, k)


def from_key(k):
    (ts_str, seq_str, tx_hash) = k.split('_')
    return (float(ts_str), int(seq_str), tx_hash, )


re_u = r'^[^_][_A-Z]+$'
class Store:

    def __init__(self, chain_spec, state_store, index_store, counter, cache=None):
        self.chain_spec = chain_spec
        self.cache = cache
        self.state_store = state_store
        self.index_store = index_store
        self.counter = counter
        for s in dir(self.state_store):
            if not re.match(re_u, s):
                continue
            v = self.state_store.from_name(s)
            setattr(self, s, v)
        for v in ['state', 'change', 'set', 'unset']:
            setattr(self, v, getattr(self.state_store, v))

        logg.debug('cache {}'.format(cache))


    def put(self, k, v, cache_adapter=CacheTx):
        n = self.counter.next()
        t = datetime.datetime.now().timestamp()
        s = to_key(t, n, k)
        self.state_store.put(s, v)
        self.index_store.put(k, s)
        if self.cache != None:
            tx = cache_adapter()
            tx.deserialize(v)
            self.cache.put(self.chain_spec, tx) 


    def get(self, k):
        s = self.index_store.get(k)
        v = self.state_store.get(s)
        return (s, v,)


    def by_state(self, state=0, limit=4096, strict=False):
        hashes = []
        i = 0

        hashes_state = self.state_store.list(state)
        if strict:
            for k in hashes_state:
                item_state = self.state_store.state(k)
                if item_state & state != item_state:
                    continue
                hashes.append(k)
        else:
            hashes = hashes_state

        hashes.sort()
        hashes_out = []
        for h in hashes:
            pair = from_key(h)
            hashes_out.append(pair[1])
        return hashes_out


    def upcoming(self, limit=4096):
        return self.by_state(state=self.QUEUED, limit=limit)
