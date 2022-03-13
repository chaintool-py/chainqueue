# standard imports
import logging
import re
import datetime

# local imports
from chainqueue.cache import CacheTx
from chainqueue.entry import QueueEntry


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
        for v in ['state', 'change', 'set', 'unset', 'name']:
            setattr(self, v, getattr(self.state_store, v))


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

        refs_state = self.state_store.list(state)
        
        for ref in refs_state:
            v = from_key(ref)
            hsh = v[2]

            if strict:
                item_state = self.state_store.state(ref)
                if item_state & state != item_state:
                    continue
            hashes.append(hsh)

        hashes.sort()
        return hashes


    def upcoming(self, limit=4096):
        return self.by_state(state=self.QUEUED, limit=limit)


    def deferred(self, limit=4096):
        return self.by_state(state=self.DEFERRED, limit=limit)


    def pending(self, limit=4096):
        return self.by_state(state=0, limit=limit, strict=True)


    def enqueue(self, k):
        entry = QueueEntry(self, k)
        entry.load()
        try:
            entry.retry()
        except StateTransitionInvalid:
            entry.readysend()
