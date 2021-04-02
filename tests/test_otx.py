# standard imports
import os
import logging
import unittest

# external imports
from hexathon import (
        strip_0x,
        add_0x,
        )
from chainlib.chain import ChainSpec

# local imports
from chainqueue.db.models.otx import Otx
from chainqueue.db.models.tx import TxCache
from chainqueue.tx import create
from chainqueue.state import *
from chainqueue.db.enum import (
        is_alive,
        is_error_status,
        )

# test imports
from tests.base import TestBase

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


class TestOtx(TestBase):

    def setUp(self):
        super(TestOtx, self).setUp()
        self.tx_hash = add_0x(os.urandom(32).hex())
        self.tx = add_0x(os.urandom(128).hex())
        self.nonce = 42
        self.alice = add_0x(os.urandom(20).hex())

        tx_hash = create(self.nonce, self.alice, self.tx_hash, self.tx, self.chain_spec, session=self.session)
        self.assertEqual(tx_hash, self.tx_hash)


    def test_ideal_state_sequence(self):
        set_ready(self.tx_hash)
        otx = Otx.load(self.tx_hash, session=self.session)
        self.assertEqual(otx.status, StatusBits.QUEUED)

        set_reserved(self.tx_hash)
        self.session.refresh(otx)
        self.assertEqual(otx.status, StatusBits.RESERVED)

        set_sent(self.tx_hash)
        self.session.refresh(otx)
        self.assertEqual(otx.status, StatusBits.IN_NETWORK)

        set_final(self.tx_hash, block=1024)
        self.session.refresh(otx)
        self.assertFalse(is_alive(otx.status))
        self.assertFalse(is_error_status(otx.status))


    def test_send_fail_and_retry(self):
        set_ready(self.tx_hash)
        otx = Otx.load(self.tx_hash, session=self.session)
        self.assertEqual(otx.status, StatusBits.QUEUED)

        set_reserved(self.tx_hash)
        self.session.refresh(otx)
        self.assertEqual(otx.status, StatusBits.RESERVED)

        set_sent(self.tx_hash, fail=True)
        self.session.refresh(otx)
        self.assertTrue(is_error_status(otx.status))

        set_ready(self.tx_hash)
        self.session.refresh(otx)
        self.assertEqual(otx.status & StatusBits.QUEUED, StatusBits.QUEUED)
        self.assertTrue(is_error_status(otx.status))

        set_reserved(self.tx_hash)
        self.session.refresh(otx)
        self.assertEqual(otx.status & StatusBits.RESERVED, StatusBits.RESERVED)
        self.assertTrue(is_error_status(otx.status))

        set_sent(self.tx_hash)
        self.session.refresh(otx)
        self.assertEqual(otx.status, StatusBits.IN_NETWORK)
        self.assertFalse(is_error_status(otx.status))

        set_final(self.tx_hash, block=1024)
        self.session.refresh(otx)
        self.assertFalse(is_alive(otx.status))
        self.assertFalse(is_error_status(otx.status))


    def test_fubar(self):
        set_ready(self.tx_hash)
        otx = Otx.load(self.tx_hash, session=self.session)
        self.assertEqual(otx.status, StatusBits.QUEUED)

        set_reserved(self.tx_hash)
        self.session.refresh(otx)
        self.assertEqual(otx.status & StatusBits.RESERVED, StatusBits.RESERVED)

        set_fubar(self.tx_hash)
        self.session.refresh(otx)
        self.assertTrue(is_error_status(otx.status))
        self.assertEqual(otx.status & StatusBits.UNKNOWN_ERROR, StatusBits.UNKNOWN_ERROR)


    def test_reject(self):
        set_ready(self.tx_hash)
        otx = Otx.load(self.tx_hash, session=self.session)
        self.assertEqual(otx.status, StatusBits.QUEUED)

        set_reserved(self.tx_hash)
        self.session.refresh(otx)
        self.assertEqual(otx.status & StatusBits.RESERVED, StatusBits.RESERVED)

        set_rejected(self.tx_hash)
        self.session.refresh(otx)
        self.assertTrue(is_error_status(otx.status))
        self.assertEqual(otx.status & StatusBits.NODE_ERROR, StatusBits.NODE_ERROR)


    def test_final_fail(self):
        set_ready(self.tx_hash)
        set_reserved(self.tx_hash)
        set_sent(self.tx_hash)
        set_final(self.tx_hash, block=1042, fail=True)
        otx = Otx.load(self.tx_hash, session=self.session)
        self.assertFalse(is_alive(otx.status))
        self.assertTrue(is_error_status(otx.status))


    def test_final_protected(self):
        set_ready(self.tx_hash)
        set_reserved(self.tx_hash)
        set_sent(self.tx_hash)
        set_final(self.tx_hash, block=1042)

        otx = Otx.load(self.tx_hash, session=self.session)
        self.assertEqual(otx.status & StatusBits.FINAL, StatusBits.FINAL)

        with self.assertRaises(TxStateChangeError):
            set_ready(self.tx_hash)

        with self.assertRaises(TxStateChangeError):
            set_fubar(self.tx_hash)

        with self.assertRaises(TxStateChangeError):
            set_rejected(self.tx_hash)

        set_cancel(self.tx_hash)
        self.session.refresh(otx)
        self.assertEqual(otx.status & StatusBits.OBSOLETE, 0)

        with self.assertRaises(TxStateChangeError):
            set_reserved(self.tx_hash)


if __name__ == '__main__':
    unittest.main()
