# standard imports
import logging
import re

logg = logging.getLogger(__name__)


def to_key(k, v):
    return '{:>010s}_{}'.format(k, v)


def from_key(k):
    (seq_str, tx_hash) = k.split('_')
    return (int(seq_str), tx_hash,)



re_u = r'^[^_][_A-Z]+$'
class Store:

    def __init__(self, state_store, index_store):
        self.state_store = state_store
        self.index_store = index_store
        for s in dir(self.state_store):
            if not re.match(re_u, s):
                continue
            v = self.state_store.from_name(s)
            setattr(self, s, v)
        for v in ['state', 'change', 'set', 'unset']:
            setattr(self, v, getattr(self.state_store, v))


    def put(self, k, n, v):
        self.index_store.put(k, n)
        k = to_key(n, k)
        self.state_store.put(k, v)


    def get(self, k):
        n = self.index_store.get(k) 
        k = to_key(n, k)
        return (k, self.state_store.get(k))


    def list(self, state=0, limit=4096, strict=False):
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
