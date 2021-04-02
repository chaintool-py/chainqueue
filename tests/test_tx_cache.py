# standard imports
import unittest

# local imports
from chainqueue.db.models.tx import TxCache
from chainqueue.error import NotLocalTxError
from chainqueue.state import *

# test imports
from tests.base import TestTxBase

class TestTxCache(TestTxBase):

    def test_mine(self):
        with self.assertRaises(NotLocalTxError):
            TxCache.set_final(self.tx_hash, 1024, 13, session=self.session)

        set_ready(self.tx_hash)
        set_reserved(self.tx_hash)
        set_sent(self.tx_hash)
        set_final(self.tx_hash, block=1024)

        with self.assertRaises(NotLocalTxError):
            TxCache.set_final(self.tx_hash, 1023, 13, session=self.session)

        TxCache.set_final(self.tx_hash, 1024, 13, session=self.session)

        self.session.commit()

        txc = TxCache.load(self.tx_hash)
        self.assertEqual(txc.tx_index, 13)


if __name__ == '__main__':
    unittest.main()
