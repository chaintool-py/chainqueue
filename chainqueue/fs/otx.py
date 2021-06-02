# local imports
from chainqueue.enum import (
        StatusEnum,
        StatusBits,
        )


class Otx:

    def __init__(self, nonce, tx_hash, signed_tx):
        self.nonce = nonce
        self.tx_hash = strip_0x(tx_hash)
        self.signed_tx = strip_0x(signed_tx)
        self.status = StatusEnum.PENDING
