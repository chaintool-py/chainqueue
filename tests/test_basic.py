# standard imports
import logging
import unittest

# test imports
from tests.base import TestBase

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()

class TestBasic(TestBase):

    def test_hello(self):
        logg.debug('foo')
        pass


if __name__ == '__main__':
    unittest.main()
