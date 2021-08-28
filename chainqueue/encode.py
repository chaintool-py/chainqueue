# standard imports
import logging

# external imports
from hexathon import (
        add_0x,
        strip_0x,
        uniform as hex_uniform,
        )

logg = logging.getLogger(__name__)


class TxHexNormalize:

    def tx_hash(self, tx_hash):
        return self.__hex_normalize(tx_hash)


    def tx_wire(self, tx_wire):
        return self.__hex_normalize(tx_wire)


    def wallet_address(self, address):
        return self.__hex_normalize(address)


    def executable_address(self, address):
        return self.__hex_normalize(address)


    def __hex_normalize(self, data):
        r = add_0x(hex_uniform(strip_0x(data)))
        logg.debug('tx hex normalize {} -> {}'.format(data, r))
        return r


class NoopNormalize:

    def __init__(self):
        self.tx_hash = self.__noop
        self.tx_wire = self.__noop
        self.wallet_address = self.__noop
        self.executable_address = self.__noop


    def __noop(self, data):
        return data
