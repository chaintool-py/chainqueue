# standard imports
import os
import logging
import unittest

# external imports
from chainlib.chain import ChainSpec

# local imports
from chainqueue.db.models.otx import Otx
from chainqueue.db.enum import (
        is_alive,
        is_error_status,
        )
from chainqueue.sql.state import *

# test imports
from tests.chainqueue_base import TestOtxBase

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


class TestOtx(TestOtxBase):

    def test_ideal_state_sequence(self):
        set_ready(self.chain_spec, self.tx_hash, session=self.session)
        otx = Otx.load(self.tx_hash, session=self.session)
        self.assertEqual(otx.status, StatusBits.QUEUED)

        set_reserved(self.chain_spec, self.tx_hash)
        self.session.refresh(otx)
        self.assertEqual(otx.status, StatusBits.RESERVED)

        set_sent(self.chain_spec, self.tx_hash, session=self.session)
        self.session.refresh(otx)
        self.assertEqual(otx.status, StatusBits.IN_NETWORK)

        set_final(self.chain_spec, self.tx_hash, block=1024, session=self.session)
        self.session.refresh(otx)
        self.assertFalse(is_alive(otx.status))
        self.assertFalse(is_error_status(otx.status))


    def test_send_fail_and_retry(self):
        set_ready(self.chain_spec, self.tx_hash, session=self.session)
        otx = Otx.load(self.tx_hash, session=self.session)
        self.assertEqual(otx.status, StatusBits.QUEUED)

        set_reserved(self.chain_spec, self.tx_hash, session=self.session)
        self.session.refresh(otx)
        self.assertEqual(otx.status, StatusBits.RESERVED)

        set_sent(self.chain_spec, self.tx_hash, fail=True, session=self.session)
        self.session.refresh(otx)
        self.assertTrue(is_error_status(otx.status))

        set_ready(self.chain_spec, self.tx_hash, session=self.session)
        self.session.refresh(otx)
        self.assertEqual(otx.status & StatusBits.QUEUED, StatusBits.QUEUED)
        self.assertTrue(is_error_status(otx.status))

        set_reserved(self.chain_spec, self.tx_hash, session=self.session)
        self.session.refresh(otx)
        self.assertEqual(otx.status & StatusBits.RESERVED, StatusBits.RESERVED)
        self.assertTrue(is_error_status(otx.status))

        set_sent(self.chain_spec, self.tx_hash, session=self.session)
        self.session.refresh(otx)
        self.assertEqual(otx.status, StatusBits.IN_NETWORK)
        self.assertFalse(is_error_status(otx.status))

        set_final(self.chain_spec, self.tx_hash, block=1024, session=self.session)
        self.session.refresh(otx)
        self.assertFalse(is_alive(otx.status))
        self.assertFalse(is_error_status(otx.status))


    def test_fubar(self):
        set_ready(self.chain_spec, self.tx_hash, session=self.session)
        otx = Otx.load(self.tx_hash, session=self.session)
        self.assertEqual(otx.status, StatusBits.QUEUED)

        set_reserved(self.chain_spec, self.tx_hash, session=self.session)
        self.session.refresh(otx)
        self.assertEqual(otx.status & StatusBits.RESERVED, StatusBits.RESERVED)

        set_fubar(self.chain_spec, self.tx_hash, session=self.session)
        self.session.refresh(otx)
        self.assertTrue(is_error_status(otx.status))
        self.assertEqual(otx.status & StatusBits.UNKNOWN_ERROR, StatusBits.UNKNOWN_ERROR)


    def test_reject(self):
        set_ready(self.chain_spec, self.tx_hash, session=self.session)
        otx = Otx.load(self.tx_hash, session=self.session)
        self.assertEqual(otx.status, StatusBits.QUEUED)

        set_reserved(self.chain_spec, self.tx_hash, session=self.session)
        self.session.refresh(otx)
        self.assertEqual(otx.status & StatusBits.RESERVED, StatusBits.RESERVED)

        set_rejected(self.chain_spec, self.tx_hash, session=self.session)
        self.session.refresh(otx)
        self.assertTrue(is_error_status(otx.status))
        self.assertEqual(otx.status & StatusBits.NODE_ERROR, StatusBits.NODE_ERROR)


    def test_final_fail(self):
        set_ready(self.chain_spec, self.tx_hash, session=self.session)
        set_reserved(self.chain_spec, self.tx_hash, session=self.session)
        set_sent(self.chain_spec, self.tx_hash, session=self.session)
        set_final(self.chain_spec, self.tx_hash, block=1042, fail=True, session=self.session)
        otx = Otx.load(self.tx_hash, session=self.session)
        self.assertFalse(is_alive(otx.status))
        self.assertTrue(is_error_status(otx.status))
        self.assertEqual(otx.status & StatusBits.NETWORK_ERROR, StatusBits.NETWORK_ERROR)


    def test_final_protected(self):
        set_ready(self.chain_spec, self.tx_hash, session=self.session)
        set_reserved(self.chain_spec, self.tx_hash, session=self.session)
        set_sent(self.chain_spec, self.tx_hash, session=self.session)
        set_final(self.chain_spec, self.tx_hash, block=1042, session=self.session)

        otx = Otx.load(self.tx_hash, session=self.session)
        self.assertEqual(otx.status & StatusBits.FINAL, StatusBits.FINAL)

        with self.assertRaises(TxStateChangeError):
            set_ready(self.chain_spec, self.tx_hash, session=self.session)

        with self.assertRaises(TxStateChangeError):
            set_fubar(self.chain_spec, self.tx_hash, session=self.session)

        with self.assertRaises(TxStateChangeError):
            set_rejected(self.chain_spec, self.tx_hash, session=self.session)

        set_cancel(self.chain_spec, self.tx_hash, session=self.session)
        self.session.refresh(otx)
        self.assertEqual(otx.status & StatusBits.OBSOLETE, 0)
        
        set_cancel(self.chain_spec, self.tx_hash, manual=True, session=self.session)
        self.session.refresh(otx)
        self.assertEqual(otx.status & StatusBits.OBSOLETE, 0)

        with self.assertRaises(TxStateChangeError):
            set_reserved(self.chain_spec, self.tx_hash, session=self.session)

        with self.assertRaises(TxStateChangeError):
            set_waitforgas(self.chain_spec, self.tx_hash, session=self.session)

        with self.assertRaises(TxStateChangeError):
            set_manual(self.chain_spec, self.tx_hash, session=self.session)


    def test_manual_persist(self):
        set_manual(self.chain_spec, self.tx_hash, session=self.session)
        set_ready(self.chain_spec, self.tx_hash, session=self.session)
        set_reserved(self.chain_spec, self.tx_hash, session=self.session)
        set_sent(self.chain_spec, self.tx_hash, session=self.session)
        set_final(self.chain_spec, self.tx_hash, block=1042, session=self.session)

        otx = Otx.load(self.tx_hash, session=self.session)
        self.assertEqual(otx.status & StatusBits.MANUAL, StatusBits.MANUAL)


if __name__ == '__main__':
    unittest.main()
