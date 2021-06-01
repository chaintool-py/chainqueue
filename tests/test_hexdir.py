# standard imports
import unittest
import tempfile
import shutil
import logging
import os

# local imports
from chainqueue.fs.dir import HexDir

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


class HexDirTest(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp() 
        self.hexdir = HexDir(self.dir, 4, 3, 2)
        logg.debug('setup hexdir root {}'.format(self.dir))
      

    def tearDown(self):
        shutil.rmtree(self.dir)
        logg.debug('cleaned hexdir root {}'.format(self.dir))


    def test_path(self):
        content = b'cdef'
        prefix = b'ab'
        label = b'\xde\xad\xbe\xef'
        self.hexdir.add(label, content, prefix=prefix)
        file_path = os.path.join(self.dir, 'DE', 'AD', 'BE', label.hex().upper())
        
        f = open(file_path, 'rb')
        r = f.read()
        f.close()
        self.assertEqual(content, r)

        f = open(self.hexdir.master_file, 'rb')
        r = f.read()
        f.close()
        self.assertEqual(prefix + label, r)


    def test_size(self):
        content = b'cdef'
        prefix = b'ab'
        label = b'\xde\xad\xbe\xef'
        with self.assertRaises(ValueError):
            self.hexdir.add(label, content, prefix=b'a')


    def test_edit(self):
        self.hexdir.add(b'\xde\xad\xbe\xef', b'foo', b'ab')
        self.hexdir.add(b'\xbe\xef\xfe\xed', b'bar', b'cd')
        self.hexdir.add(b'\x01\x02\x03\x04', b'baz', b'ef')
        self.hexdir.set_prefix(1, b'ff')

        f = open(self.hexdir.master_file, 'rb')
        f.seek(6)
        r = f.read(2)
        f.close()
        self.assertEqual(b'ff', r)


if __name__ == '__main__':
    unittest.main()
