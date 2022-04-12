# standard imports
import re
import datetime
import logging

# local imports
from chainqueue.cache import CacheTx
from chainqueue.entry import QueueEntry
from chainqueue.error import (
        NotLocalTxError,
        )

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
        for v in [
                'state',
                'change',
                'set',
                'unset',
                'name',
                'modified',
                ]:
            setattr(self, v, getattr(self.state_store, v))
        self.state_store.sync()


    def put(self, v, cache_adapter=CacheTx):
        tx = cache_adapter(self.chain_spec)
        tx.deserialize(v)
        k = tx.hash
        n = self.counter.next()
        t = datetime.datetime.now().timestamp()
        s = to_key(t, n, k)
        self.index_store.put(k, s)
        self.state_store.put(s, v)
        if self.cache != None:
            self.cache.put(self.chain_spec, tx) 
        return (s, k,)


    def get(self, k):
        try:
            s = self.index_store.get(k)
        except FileNotFoundError:
            raise NotLocalTxError(k)
        v = self.state_store.get(s)
        return (s, v,)


    def by_state(self, state=0, limit=4096, strict=False, threshold=None):
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

            if threshold != None:
                v = self.state_store.modified(ref)
                if v > threshold:
                    continue

            hashes.append(hsh)



        hashes.sort()
        return hashes


    def upcoming(self, limit=4096):
        return self.by_state(state=self.QUEUED, limit=limit)


    def deferred(self, limit=4096, threshold=None):
        return self.by_state(state=self.DEFERRED, limit=limit, threshold=threshold)


    def pending(self, limit=4096):
        return self.by_state(state=0, limit=limit, strict=True)


    def reserve(self, k):
        entry = QueueEntry(self, k)
        entry.load()
        entry.reserve()


    def enqueue(self, k):
        entry = QueueEntry(self, k)
        entry.load()
        try:
            entry.retry()
        except StateTransitionInvalid:
            entry.readysend()


    def fail(self, k):
        entry = QueueEntry(self, k)
        entry.load()
        entry.sendfail()


    def final(self, k, block, tx, error=False):
        entry = QueueEntry(self, k)
        entry.load()
        if error:
            entry.fail(block, tx)
        else:
            entry.succeed(block, tx)


    def send_start(self, k):
        entry = QueueEntry(self, k)
        entry.load()
        entry.reserve()
        return entry


    def send_end(self, k):
        entry = QueueEntry(self, k)
        entry.load()
        entry.sent()
