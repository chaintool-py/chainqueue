# standard imports
import logging
import re

logg = logging.getLogger(__name__)


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
        for v in ['put', 'get', 'state', 'change', 'set', 'unset']:
            setattr(self, v, getattr(self.state_store, v))


    def put(self, k, v):
        self.state_store.put(k, v)


    def get(self, k, v):
        return self.state_store.get(k)


    def put_seq(self, k, seq):
        self.index_store.put(k, seq)


    def get_seq(self, k):
        return self.index_store.get(k)


    def list(self, state=0, limit=4096, strict=False):
        hashes = []
        i = 0
        for k in self.state_store.list(state):
            item_state = self.state_store.state(k)
            if strict:
                if item_state & state != item_state:
                    continue
            hashes.append(k)
        return hashes
