# standard imports
import tempfile
import unittest
import shutil
import logging

# external imports
from shep.store.file import SimpleFileStoreFactory
from chainlib.chain import ChainSpec

# local imports
from chainqueue import (
        Store,
        Status,
        )

# test imports
from tests.common import (
        MockCounter,
        MockContentStore,
        )

logg = logging.getLogger(__name__)

class TestShepBase(unittest.TestCase):

    def setUp(self):
        self.path = tempfile.mkdtemp()
        factory = SimpleFileStoreFactory(self.path).add
        self.state = Status(factory)
        content_store = MockContentStore()
        counter = MockCounter()
        chain_spec = ChainSpec('foo', 'bar', 42, 'baz')
        self.store = Store(chain_spec, self.state, content_store, counter)
        logg.debug('using path {}'.format(self.path))


    def tearDown(self):
        shutil.rmtree(self.path)
