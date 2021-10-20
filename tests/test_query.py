# standard imports
import os
import logging
import unittest

# external imports
from hexathon import (
        add_0x,
        strip_0x,
        )

# local imports
from chainqueue.sql.query import *
from chainqueue.sql.tx import create
from chainqueue.sql.state import (
        set_waitforgas,
        set_ready,
        set_reserved,
        set_sent,
        set_final,
        )
from chainqueue.enum import StatusBits

# test imports
from tests.chainqueue_base import TestTxBase

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
                self.chain_spec,
                42,
                self.alice,
                tx_hash,
                signed_tx,
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
                self.chain_spec,
                41,
                self.alice,
                tx_hash,
                signed_tx,
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
        set_waitforgas(self.chain_spec, self.tx_hash)
        
        tx_hash = add_0x(os.urandom(32).hex())
        signed_tx = add_0x(os.urandom(128).hex())
        create(
                self.chain_spec,
                43,
                self.alice,
                tx_hash,
                signed_tx,
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
                self.chain_spec,
                42,
                self.bob,
                tx_hash,
                signed_tx,
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

        set_waitforgas(self.chain_spec, tx_hash)
        self.session.commit()

        txs = get_paused_tx_cache(self.chain_spec, status=StatusBits.GAS_ISSUES, session=self.session)
        self.assertEqual(len(txs.keys()), 2)

        txs = get_paused_tx_cache(self.chain_spec, status=StatusBits.GAS_ISSUES, sender=self.bob, session=self.session)
        self.assertEqual(len(txs.keys()), 1)


    def test_count(self):
        for i in range(3):
            tx_hash = add_0x(os.urandom(32).hex())
            signed_tx = add_0x(os.urandom(128).hex())
            create(
                    self.chain_spec,
                    i,
                    self.alice,
                    tx_hash,
                    signed_tx,
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
            set_ready(self.chain_spec, tx_hash, session=self.session)
            set_reserved(self.chain_spec, tx_hash, session=self.session)
            if i > 0:
                set_sent(self.chain_spec, tx_hash, session=self.session)
            if i == 2:
                set_final(self.chain_spec, tx_hash, session=self.session)

        tx_hash = add_0x(os.urandom(32).hex())
        signed_tx = add_0x(os.urandom(128).hex())
        create(
                self.chain_spec,
                i,
                self.bob,
                tx_hash,
                signed_tx,
                session=self.session,
                )
        txc = TxCache(
            tx_hash,
            self.bob,
            self.carol,
            self.foo_token,
            self.bar_token,
            self.from_value,
            self.to_value,
            session=self.session,
            )

        self.session.add(txc)
        set_ready(self.chain_spec, tx_hash, session=self.session)
        set_reserved(self.chain_spec, tx_hash, session=self.session)
        set_sent(self.chain_spec, tx_hash, session=self.session)
        self.session.commit()

        self.assertEqual(count_tx(self.chain_spec, status=StatusBits.IN_NETWORK | StatusBits.FINAL, status_target=StatusBits.IN_NETWORK), 2)
        self.assertEqual(count_tx(self.chain_spec, sender=self.alice, status=StatusBits.IN_NETWORK | StatusBits.FINAL, status_target=StatusBits.IN_NETWORK), 1)


    def test_account_tx(self):

        nonce_hashes = [self.tx_hash]
        tx_hash = add_0x(os.urandom(32).hex())
        signed_tx = add_0x(os.urandom(128).hex())
        create(
                self.chain_spec,
                42,
                self.alice,
                tx_hash,
                signed_tx,
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

        time_between = datetime.datetime.utcnow()

        tx_hash = add_0x(os.urandom(32).hex())
        signed_tx = add_0x(os.urandom(128).hex())
        create(
                self.chain_spec,
                41,
                self.alice,
                tx_hash,
                signed_tx,
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

        nonce_hashes.append(tx_hash)

        txs = get_account_tx(self.chain_spec, self.alice, as_sender=True, as_recipient=False, session=self.session)
        self.assertEqual(len(txs.keys()), 3)
         
        txs = get_account_tx(self.chain_spec, self.alice, as_sender=True, as_recipient=False, session=self.session, since=tx_hash)
        self.assertEqual(len(txs.keys()), 1)

        txs = get_account_tx(self.chain_spec, self.alice, as_sender=True, as_recipient=False, session=self.session, since=nonce_hashes[0])
        self.assertEqual(len(txs.keys()), 3)

        bogus_hash = add_0x(os.urandom(32).hex())
        txs = get_account_tx(self.chain_spec, self.alice, as_sender=True, as_recipient=False, session=self.session, since=bogus_hash)
        self.assertEqual(len(txs.keys()), 0)

        txs = get_account_tx(self.chain_spec, self.alice, as_sender=True, as_recipient=False, session=self.session, since=time_between)
        self.assertEqual(len(txs.keys()), 1)

        time_before = time_between - datetime.timedelta(hours=1)
        txs = get_account_tx(self.chain_spec, self.alice, as_sender=True, as_recipient=False, session=self.session, since=time_before)
        self.assertEqual(len(txs.keys()), 3)

        time_after = datetime.datetime.utcnow()
        txs = get_account_tx(self.chain_spec, self.alice, as_sender=True, as_recipient=False, session=self.session, since=time_after)
        self.assertEqual(len(txs.keys()), 0)


        txs = get_account_tx(self.chain_spec, self.alice, as_sender=True, as_recipient=False, session=self.session, since=2)
        self.assertEqual(len(txs.keys()), 2)

        txs = get_account_tx(self.chain_spec, self.alice, as_sender=True, as_recipient=False, session=self.session, since=1)
        self.assertEqual(len(txs.keys()), 3)

        txs = get_account_tx(self.chain_spec, self.alice, as_sender=True, as_recipient=False, session=self.session, since=4)
        self.assertEqual(len(txs.keys()), 0)

        txs = get_account_tx(self.chain_spec, self.alice, as_sender=True, as_recipient=False, session=self.session, since=1, until=2)
        self.assertEqual(len(txs.keys()), 2)

        txs = get_account_tx(self.chain_spec, self.alice, as_sender=True, as_recipient=False, session=self.session, since=time_before, until=time_between)
        self.assertEqual(len(txs.keys()), 2)

        txs = get_account_tx(self.chain_spec, self.alice, as_sender=True, as_recipient=False, session=self.session, since=nonce_hashes[0], until=nonce_hashes[1])
        self.assertEqual(len(txs.keys()), 2)

        txs = get_account_tx(self.chain_spec, self.alice, as_sender=True, as_recipient=False, status=StatusBits.QUEUED, session=self.session)
        self.assertEqual(len(txs.keys()), 0)

        set_ready(self.chain_spec, nonce_hashes[1], session=self.session)
        txs = get_account_tx(self.chain_spec, self.alice, as_sender=True, as_recipient=False, status=StatusBits.QUEUED, session=self.session)
        self.assertEqual(len(txs.keys()), 1)

        set_reserved(self.chain_spec, nonce_hashes[1], session=self.session)
        set_sent(self.chain_spec, nonce_hashes[1], session=self.session)
        txs = get_account_tx(self.chain_spec, self.alice, as_sender=True, as_recipient=False, status=StatusBits.QUEUED, session=self.session)
        self.assertEqual(len(txs.keys()), 0)

        txs = get_account_tx(self.chain_spec, self.alice, as_sender=True, as_recipient=False, not_status=StatusBits.QUEUED, session=self.session)
        self.assertEqual(len(txs.keys()), 3)

        txs = get_account_tx(self.chain_spec, self.alice, as_sender=True, as_recipient=False, not_status=StatusBits.QUEUED, status=StatusBits.IN_NETWORK, session=self.session)
        self.assertEqual(len(txs.keys()), 1)


if __name__ == '__main__':
    unittest.main()
