# standard imports
import unittest
import tempfile
import shutil
import logging
import os

# local imports
from chainqueue.fs.cache import FsQueue
from chainqueue.fs.dir import HexDir

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


class HexDirTest(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp() 
        self.hexdir = HexDir(os.path.join(self.dir, 'q'), 32, 2, 8)
        self.q = FsQueue(os.path.join(self.dir, 'spool'), backend=self.hexdir)
        logg.debug('setup fsqueue root {}'.format(self.dir))


    def tearDown(self):
        shutil.rmtree(self.dir)
        logg.debug('cleaned fsqueue root {}'.format(self.dir))


    def test_new(self):
        tx_hash = os.urandom(32)
        tx_content = os.urandom(128)
        self.q.add(tx_hash, tx_content)

        f = open(os.path.join(self.q.path_state['new'], tx_hash.hex()), 'rb')
        r = f.read()
        f.close()
        self.assertEqual(r, b'\x00' * 8)


if __name__ == '__main__':
    unittest.main()
