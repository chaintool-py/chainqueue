# external imports
from chainlib.eth.tx import (
        unpack,
        )
from hexathon import add_0x

# local imports


class EthAdapter:

    def __init__(self, backend):
        self.backend = backend


    def add(self, chain_spec, bytecode):
        tx = unpack(bytecode, chain_spec)
        session = self.backend.create_session()
        self.backend.create(chain_spec, tx['nonce'], tx['from'], tx['hash'], add_0x(bytecode.hex()), session=session)
        session.close()
