# standard imports
import unittest
import tempfile
import shutil
import logging
import os

# external imports
from leveldir.hex import HexDir

# local imports
from chainqueue.fs.queue import FsQueue
from chainqueue.fs.entry import Entry
from chainqueue.enum import StatusBits

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


class FsQueueEntryTest(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp() 
        self.hexdir = HexDir(os.path.join(self.dir, 'q'), 32, 2, 8)
        self.q = FsQueue(os.path.join(self.dir, 'spool'), backend=self.hexdir)
        logg.debug('setup fsqueue root {}'.format(self.dir))


    def tearDown(self):
        shutil.rmtree(self.dir)
        logg.debug('cleaned fsqueue root {}'.format(self.dir))


    def test_entry(self):
        tx_hash = os.urandom(32).hex()
        tx_content = os.urandom(128).hex()
        Entry(0, tx_hash, tx_content)


if __name__ == '__main__':
    unittest.main()
