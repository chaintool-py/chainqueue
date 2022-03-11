class Tx:

    def __init__(self, store, seq, tx_hash, signed_tx, cache=None):
        self.store = store
        self.seq = seq
        self.tx_hash = tx_hash
        self.signed_tx = signed_tx
        self.cache = cache


    def __to_key(self, k, v):
        return '{:>010s}_{}'.format(k, v)


    def create(self):
        k = self.__to_key(str(self.seq), self.tx_hash)
        self.store.put(k, self.signed_tx)


    def waitforgas(self):
        pass
