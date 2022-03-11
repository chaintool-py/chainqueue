class Cache: 
   
    def put(self, chain_spec, tx):
        raise NotImplementedError()


    def get(self, chain_spec, tx_hash):
        raise NotImplementedError()
