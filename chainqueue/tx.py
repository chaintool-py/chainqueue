# standard imports
import logging

logg = logging.getLogger(__name__)


class Tx:

    def __init__(self, store, seq, tx_hash, signed_tx, cache=None):
        self.store = store
        self.seq = seq
        self.tx_hash = tx_hash
        self.signed_tx = signed_tx
        self.cache = cache
        self.k = self.__to_key(str(seq), tx_hash)


    def __to_key(self, k, v):
        return '{:>010s}_{}'.format(k, v)


    def create(self):
        self.store.put(self.k, self.signed_tx)


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


    def override(self):
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

