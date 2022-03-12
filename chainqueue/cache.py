class CacheTx:

    def __init__(self):
        self.v_sender = None
        self.v_recipient = None
        self.v_nonce = None
        self.v_value = None

        self.block_number = None
        self.tx_index = None
        self.timestamp = None


    def confirm(self, block_number, tx_index, timestamp):
        self.block_number = block_number
        self.tx_index = tx_index
        self.timestamp = timestamp


    def init(self, nonce, sender, recipient, value):
        self.v_sender = sender
        self.v_recipient = recipient
        self.v_nonce = nonce
        self.v_value = value


    def deserialize(self, signed_tx):
        raise NotImplementedError()


    def set(self, k, v):
        k = 'v_' + k
        setattr(self, k, v)


    def __str__(self):
        return '{} -> {} : {}'.format(self.v_sender, self.v_recipient, self.v_value)



class CacheTokenTx(CacheTx):

    def __init__(self): #, nonce, sender, recipient, src_token, dst_token, src_value, dst_value):
        super(CacheTokenTx, self).__init__()
        self.v_src_token = None
        self.v_src_value = None
        self.v_dst_token = None
        self.v_dst_value = None



class Cache: 

    def __init__(self, translator):
        self.translator = translator
 

    def put_serialized(self, chain_spec, signed_tx):
        cache_tx = self.translate(chain_spec, signed_tx)
        return self.put(chain_spec, cache_tx)


    def put(self, chain_spec, cache_tx):
        raise NotImplementedError()


    def get(self, chain_spec, tx_hash):
        raise NotImplementedError()
