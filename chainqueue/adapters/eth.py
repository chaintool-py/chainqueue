# external imports
from chainlib.eth.constant import ZERO_ADDRESS
from chainlib.eth.tx import (
        unpack,
        )
from hexathon import (
        add_0x,
        strip_0x,
        )

# local imports
from chainqueue.adapters.base import Adapter
from chainqueue.enum import StatusBits


class EthAdapter(Adapter):


    def translate(self, chain_spec, bytecode):
        tx = unpack(bytecode, chain_spec)
        tx['source_token'] = ZERO_ADDRESS
        tx['destination_token'] = ZERO_ADDRESS
        tx['from_value'] = tx['value']
        tx['to_value'] = tx['value']
        return tx


    def add(self, chain_spec, bytecode):
        tx = self.translate(chain_spec, bytecode)
        session = self.backend.create_session()
        r = self.backend.create(chain_spec, tx['nonce'], tx['from'], tx['hash'], add_0x(bytecode.hex()), session=session)
        if r:
            session.rollback()
            session.close()
            return r
        r = self.backend.cache(tx, session=session)
        session.commit()
        session.close()
        return r


    def cache(self, chain_spec):
        session = self.backend.create_session()
        r = self.backend.create(chain_spec, tx['nonce'], tx['from'], tx['hash'], add_0x(bytecode.hex()), session=session)
        session.close()


    def process(self, chain_spec):
        return self.backend.get(chain_spec, StatusBits.QUEUED, unpack)
