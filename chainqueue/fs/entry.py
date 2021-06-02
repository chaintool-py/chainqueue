# standard imports
import datetime

# external imports
from hexathon import strip_0x

# local imports
from chainqueue.enum import StatusEnum


class DefaultApplier:

    def add(self, tx_hash, signed_tx):
        logg.debug('noop add {} {}'.format(tx_hash, signed_tx))


class Entry:

    def __init__(self, nonce, tx_hash, signed_tx, applier=DefaultApplier()):
        self.nonce = nonce
        self.tx_hash = strip_0x(tx_hash)
        self.signed_tx = strip_0x(signed_tx)
        self.status = StatusEnum.PENDING

        self.applier.add(bytes.fromhex(tx_hash), bytes.fromhex(signed_tx))


class MetaEntry:

    def __init__(self, entry, sender, recipient, source_token_address, destination_token_address, from_value, to_value, block_number=None, tx_index=None, date_created=datetime.datetime.utcnow()):
        self.entry = entry
        self.sender = sender
        self.recipient = recipient
        self.source_token_address = source_token_address
        self.destination_token_address = destination_token_address
        self.from_value = from_value
        self.to_value = to_value
        self.block_number = block_number
        self.tx_index = tx_index
        self.date_created = date_created
        self.date_updated = self.date_created
