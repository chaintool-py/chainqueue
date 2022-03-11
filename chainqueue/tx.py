# standard imports
import logging

logg = logging.getLogger(__name__)


class Tx:

    def __init__(self, state_store, index_store, tx_hash, cache=None):
        self.state_store = state_store
        self.index_store = index_store
        self.cache = cache
        self.tx_hash = tx_hash
        self.signed_tx = None
        self.seq = None
        self.k = None
        self.synced = False


    def __to_key(self, k, v):
        return '{:>010s}_{}'.format(k, v)


    def create(self, seq, signed_tx):
        n = str(seq)
        self.k = self.__to_key(n, self.tx_hash)
        self.state_store.put(self.k, signed_tx)
        self.index_store.put(self.tx_hash, n)
        self.synced = True


    def load(self):
        seq = self.index_store.get(self.tx_hash)
        self.k = self.__to_key(seq, self.tx_hash)
        self.signed_tx = self.state_store.get(self.k)
        self.synced = True


    def __match_state(self, state):
        return bool(self.store.state(self.k) & state)

    
    def waitforfunds(self):
        if self.__match_state(self.store.INSUFFICIENT_FUNDS):
            return
        self.state.move(self.k, self.store.INSUFFICIENT_FUNDS)


    def fubar(self):
        if self.__match_state(self.store.UNKNOWN_ERROR):
            return
        self.state.set(self.k, self.store.UNKNOWN_ERROR)


    def reject(self):
        if self.__match_state(self.store.NODE_ERROR):
            return
        self.state.set(self.k, self.store.NODE_ERROR)


    def override(self, manual=False):
        if manual:
            self.state.set(self.k, self.store.OBSOLETE | self.store.MANUAL)
        else:
            self.state.set(self.k, self.store.OBSOLETE)


    def manual(self):
        self.state.set(self.k, self.store.MANUAL)


    def retry(self):
        if self.__match_state(self.store.QUEUED):
            return
        self.state.change(self.k, self.store.QUEUED, self.store.INSUFFICIENT_FUNDS)


    def readysend(self):
        if self.__match_state(self.store.QUEUED):
            return
        self.state.change(self.k, self.store.QUEUED, self.store.INSUFFICIENT_FUNDS)

    
    def sent(self):
        if self.__match_state(self.store.IN_NETWORK):
            return
        self.state.change(self.k, self.state.IN_NETWORK, self.state.RESERVED | self.state.DEFERRED | self.state.QUEUED | self.state.LOCAL_ERROR | self.state.NODE_ERROR)


    def sendfail(self):
        if self.__match_state(self.store.NODE_ERROR):
            return
        self.state.change(self.k, self.state.LOCAL_ERROR | self.state.DEFERRED, self.state.RESERVED | self.state.QUEUED | self.state.INSUFFICIENT_FUNDS)


    def reserve(self):
        if self.__match_state(self.store.RESERVED):
            return
        self.state.change(self.k, self.state.RESERVED, self.state.QUEUED) 


    def minefail(self, block):
        if self.__match_state(self.store.NETWORK_ERROR):
            return
        self.state.set(self.k, self.state.NETWORK_ERROR)
        if self.cache:
            self.cache.set_block(self.tx_hash, block)


    def cancel(self, confirmed=False):
        if confirmed:
            self.state.change(self.k, self.state.OBSOLETE | self.state.FINAL, self.state.RESERVED | self.state.QUEUED)
        else:
            self.state.change(self.k, self.state.OBSOLETE, self.state.RESERVED | self.state.QUEUED)


    def success(self, block):
        self.state.set(self.state.FINAL)
        if self.cache:
            self.cache.set_block(self.tx_hash, block)


    def get(status=0, limit=4096, status_exact=True):
        hashes = []
        i = 0
        for k in self.state.list(status):
            if status_exact:
                if self.state.status(k) != status:
                    continue
            hashes.append(k)
        return k
