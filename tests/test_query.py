# standard imports
import os
import logging
import unittest

# local imports
from chainqueue.query import *
from chainqueue.tx import create
from chainqueue.state import set_waitforgas
from hexathon import (
        add_0x,
        strip_0x,
        )

# test imports
from tests.base import TestTxBase

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


class TestTxQuery(TestTxBase):

    def test_get_tx(self):
        tx = get_tx(self.chain_spec, self.tx_hash) 
        expected_keys = [
                'otx_id',
                'status',
                'signed_tx',
                'nonce',
                ]
        for k in tx.keys():
            expected_keys.remove(k)

        self.assertEqual(len(expected_keys), 0)


    def test_nonce_tx(self):

        nonce_hashes = [self.tx_hash]
        tx_hash = add_0x(os.urandom(32).hex())
        signed_tx = add_0x(os.urandom(128).hex())
        create(
                42,
                self.alice,
                tx_hash,
                signed_tx,
                self.chain_spec,
                session=self.session,
                )
        txc = TxCache(
                tx_hash,
                self.alice,
                self.bob,
                self.foo_token,
                self.bar_token,
                self.from_value,
                self.to_value,
                session=self.session,
                )
        self.session.add(txc)
        self.session.commit()

        nonce_hashes.append(tx_hash)

        tx_hash = add_0x(os.urandom(32).hex())
        signed_tx = add_0x(os.urandom(128).hex())
        create(
                41,
                self.alice,
                tx_hash,
                signed_tx,
                self.chain_spec,
                session=self.session,
                )
        txc = TxCache(
                tx_hash,
                self.alice,
                self.bob,
                self.foo_token,
                self.bar_token,
                self.from_value,
                self.to_value,
                session=self.session,
                )
        self.session.add(txc)

        txs = get_nonce_tx_cache(self.chain_spec, 42, self.alice)
        self.assertEqual(len(txs.keys()), 2)
    
        for h in nonce_hashes:
            self.assertTrue(strip_0x(h) in txs)


    def test_paused_tx_cache(self):
        set_waitforgas(self.tx_hash)
        
        tx_hash = add_0x(os.urandom(32).hex())
        signed_tx = add_0x(os.urandom(128).hex())
        create(
                43,
                self.alice,
                tx_hash,
                signed_tx,
                self.chain_spec,
                session=self.session,
                )
        txc = TxCache(
                tx_hash,
                self.alice,
                self.bob,
                self.foo_token,
                self.bar_token,
                self.from_value,
                self.to_value,
                session=self.session,
                )
        self.session.add(txc)
        self.session.commit()

        txs = get_paused_tx_cache(self.chain_spec, status=StatusBits.GAS_ISSUES, sender=self.alice, session=self.session)
        self.assertEqual(len(txs.keys()), 1)

        txs = get_paused_tx_cache(self.chain_spec, status=StatusBits.GAS_ISSUES, session=self.session)
        self.assertEqual(len(txs.keys()), 1)

        tx_hash = add_0x(os.urandom(32).hex())
        signed_tx = add_0x(os.urandom(128).hex())
        create(
                42,
                self.bob,
                tx_hash,
                signed_tx,
                self.chain_spec,
                session=self.session,
                )
        txc = TxCache(
                tx_hash,
                self.bob,
                self.alice,
                self.bar_token,
                self.foo_token,
                self.to_value,
                self.from_value,
                session=self.session,
                )
        self.session.add(txc)
        self.session.commit()

        txs = get_paused_tx_cache(self.chain_spec, status=StatusBits.GAS_ISSUES, session=self.session)
        self.assertEqual(len(txs.keys()), 1)

        set_waitforgas(tx_hash)
        self.session.commit()

        txs = get_paused_tx_cache(self.chain_spec, status=StatusBits.GAS_ISSUES, session=self.session)
        self.assertEqual(len(txs.keys()), 2)

        txs = get_paused_tx_cache(self.chain_spec, status=StatusBits.GAS_ISSUES, sender=self.bob, session=self.session)
        self.assertEqual(len(txs.keys()), 1)


if __name__ == '__main__':
    unittest.main()
