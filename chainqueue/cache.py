# standard imports
import enum


class CacheTx:

    def __init__(self):
        self.sender = None
        self.recipient = None
        self.nonce = None
        self.value = None

        self.tx_hash = None
        self.block_number = None
        self.tx_index = None
        self.timestamp = None


    def confirm(self, block_number, tx_index, timestamp):
        self.block_number = block_number
        self.tx_index = tx_index
        self.timestamp = timestamp


    def init(self, tx_hash, nonce, sender, recipient, value):
        self.tx_hash = tx_hash
        self.sender = sender
        self.recipient = recipient
        self.nonce = nonce
        self.value = value


    def deserialize(self, signed_tx):
        raise NotImplementedError()


    def set(self, k, v):
        k = 'v_' + k
        setattr(self, k, v)


    def __str__(self):
        return '{}: {} ({}) -> {} = {}'.format(self.tx_hash, self.sender, self.nonce, self.recipient, self.value)



class CacheTokenTx(CacheTx):

    def __init__(self): #, nonce, sender, recipient, src_token, dst_token, src_value, dst_value):
        super(CacheTokenTx, self).__init__()
        self.v_src_token = None
        self.v_src_value = None
        self.v_dst_token = None
        self.v_dst_value = None


class CacheSort(enum.Enum):
    DATE = 1
    NONCE = 2


class CacheFilter:

    def __init__(self, senders=None, recipients=None, nonce=None, before=None, after=None, sort=CacheSort.DATE, reverse=False):
        self.senders = senders
        self.recipients = recipients
        self.nonce = nonce
        self.before = before
        self.after = after
        self.sort = sort
        self.reverse = reverse


class Cache: 

    def put(self, chain_spec, cache_tx):
        raise NotImplementedError()


    def get(self, chain_spec, tx_hash):
        raise NotImplementedError()


    def by_nonce(self, cache_filter):
        raise NotImplementedError()


    def by_date(self, cache_filter=None):
        raise NotImplementedError()


    def count(self, cache_filter=None):
        raise NotImplementedError()
