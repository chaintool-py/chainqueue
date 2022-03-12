# standard imports
import enum
import logging

logg = logging.getLogger(__name__)


class NoopNormalizer:

    def __init__(self):
        self.address = self.noop
        self.hash = self.noop
        self.value = self.noop


    def noop(self, v):
        return v


noop_normalizer = NoopNormalizer()


class CacheTx:

    def __init__(self, normalizer=noop_normalizer):
        self.normalizer = normalizer
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
        self.tx_hash = self.normalizer.hash(tx_hash)
        self.sender = self.normalizer.address(sender)
        self.recipient = self.normalizer.address(recipient)
        self.nonce = nonce
        self.value = self.normalizer.value(value)


    def deserialize(self, signed_tx):
        raise NotImplementedError()


    def set(self, k, v):
        k = 'v_' + k
        setattr(self, k, v)


    def __str__(self):
        return '{}: {} ({}) -> {} = {}'.format(self.tx_hash, self.sender, self.nonce, self.recipient, self.value)



class CacheTokenTx(CacheTx):

    def __init__(self, normalizer=noop_normalizer):
        super(CacheTokenTx, self).__init__(normalizer=normalizer)
        self.v_src_token = None
        self.v_src_value = None
        self.v_dst_token = None
        self.v_dst_value = None


class CacheSort(enum.Enum):
    DATE = 1
    NONCE = 2


class CacheFilter:

    def __init__(self, normalizer=noop_normalizer, nonce=None, before=None, after=None, sort=CacheSort.DATE, reverse=False):
        self.normalizer = normalizer
        self.senders = None
        self.recipients = None
        self.nonce = nonce
        self.before = before
        self.after = after
        self.sort = sort
        self.reverse = reverse


    def add_senders(self, senders):
        if self.senders == None:
            self.senders = []
        if isinstance(senders, str):
            senders = [senders]
        for sender in senders:
            if self.normalizer != None:
                sender = self.normalizer.address(sender)
            self.senders.append(sender)


    def add_recipients(self, recipients):
        if self.recipients == None:
            self.recipients = []
        if isinstance(recipients, str):
            recipients = [recipients]
        for recipient in recipients:
            if self.normalizer != None:
                recipient = self.normalizer.address(recipient)
            self.recipients.append(recipient)


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
