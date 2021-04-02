# standard imports
import unittest

# local imports
from chainqueue.db.models.otx import Otx
from chainqueue.state import *

# test imports
from tests.base import TestOtxBase


class TestOtxState(TestOtxBase):


    def setUp(self):
        super(TestOtxState, self).setUp()
        Otx.tracing = True
        logg.debug('state trace')
   

    def test_state_log(self):
        set_ready(self.tx_hash)
        set_reserved(self.tx_hash)
        set_sent(self.tx_hash)
        set_final(self.tx_hash, block=1042)

        state_log = get_state_log(self.chain_spec, self.tx_hash)
        self.assertEqual(state_log[0][1], StatusEnum.READYSEND)
        self.assertEqual(state_log[1][1], StatusEnum.RESERVED)
        self.assertEqual(state_log[2][1], StatusEnum.SENT)
        self.assertEqual(state_log[3][1], StatusEnum.SUCCESS)


if __name__ == '__main__':
    unittest.main()
