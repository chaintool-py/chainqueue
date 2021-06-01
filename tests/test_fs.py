# standard imports
import unittest
import tempfile
import shutil
import logging
import os

# local imports
from chainqueue.fs.cache import FsQueue
from chainqueue.fs.dir import HexDir
from chainqueue.enum import StatusBits

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

    
    def test_change(self):
        tx_hash = os.urandom(32)
        tx_content = os.urandom(128)
        self.q.add(tx_hash, tx_content)
        self.q.set(tx_hash, StatusBits.QUEUED)
        
        (tx_status, tx_content_retrieved) = self.q.get(tx_hash)
        status = int.from_bytes(tx_status, byteorder='big')
        self.assertEqual(status & StatusBits.QUEUED, StatusBits.QUEUED)


    def test_move(self):
        tx_hash = os.urandom(32)
        tx_content = os.urandom(128)
        self.q.add(tx_hash, tx_content)
        self.q.move(tx_hash, 'ready', from_state='new')
       
        f = open(os.path.join(self.q.path_state['ready'], tx_hash.hex()), 'rb')
        r = f.read()
        f.close()
        self.assertEqual(r, b'\x00' * 8)


    def test_purge(self):
        tx_hash = os.urandom(32)
        tx_content = os.urandom(128)
        self.q.add(tx_hash, tx_content)
        self.q.move(tx_hash, 'ready', from_state='new')
        self.q.purge(tx_hash, 'ready')
      
        with self.assertRaises(FileNotFoundError):
            entry_path = os.path.join(self.q.path_state['ready'], tx_hash.hex())
            os.stat(entry_path)

        with self.assertRaises(FileNotFoundError):
            entry_path = os.path.join(self.q.index_path, tx_hash.hex())
            os.stat(entry_path)


if __name__ == '__main__':
    unittest.main()
