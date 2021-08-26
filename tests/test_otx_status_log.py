# standard imports
import unittest

# local imports
from chainqueue.db.models.otx import Otx
from chainqueue.sql.state import *

# test imports
from tests.chainqueue_base import TestOtxBase


class TestOtxState(TestOtxBase):


    def setUp(self):
        super(TestOtxState, self).setUp()
        Otx.tracing = True
        logg.debug('state trace')
   

    def test_state_log(self):
        set_ready(self.chain_spec, self.tx_hash, session=self.session)
        set_reserved(self.chain_spec, self.tx_hash, session=self.session)
        set_sent(self.chain_spec, self.tx_hash, session=self.session)
        set_final(self.chain_spec, self.tx_hash, block=1042, session=self.session)

        state_log = get_state_log(self.chain_spec, self.tx_hash)
        self.assertEqual(state_log[0][1], StatusEnum.READYSEND)
        self.assertEqual(state_log[1][1], StatusEnum.RESERVED)
        self.assertEqual(state_log[2][1], StatusEnum.SENT)
        self.assertEqual(state_log[3][1], StatusEnum.SUCCESS)


if __name__ == '__main__':
    unittest.main()
