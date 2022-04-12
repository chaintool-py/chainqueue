# standard imports
import os
import logging

# external imports
from leveldir.hex import HexDir

# local imports
from chainqueue.error import DuplicateTxError

logg = logging.getLogger(__name__)


class IndexStore(HexDir):

    def __init__(self, root_path, digest_bytes=32):
        os.path.join(root_path, 'contents')
        self.store = HexDir(root_path, digest_bytes)

    
    def __exists(self, k):
        existing = None
        try:
            existing = self.get(k)
        except FileNotFoundError:
            pass
        return existing != None


    def put(self, k, v):
        kb = bytes.fromhex(k)
        vb = v.encode('utf-8')
        if self.__exists(k):
            raise DuplicateTxError(k)
        self.store.add(kb, vb)


    def get(self, k):
        fp = self.store.to_filepath(k)
        f = open(fp, 'rb')
        v = f.read()
        f.close()
        return v.decode('utf-8')


class CounterStore:

    def __init__(self, root_path):
        try:
            os.stat(root_path)
        except FileNotFoundError:
            os.makedirs(root_path)

        fp = os.path.join(root_path, '.counter')
        f = None
        try:
            f = open(fp, 'rb+')
        except FileNotFoundError:
            logg.debug('counter not found, creating new in {}'.format(fp))
            f = open(fp, 'wb+')
            f.write(b'\x00' * 8)
            f.close()
            f = open(fp, 'rb+')
    
        v = f.read(8)
        self.count = int.from_bytes(v, byteorder='big')
        logg.info('counter starts at {}'.format(self.count))
    
        f.seek(0)

        self.f = f


    def __del__(self):
        self.f.close()


    def next(self):
        c = self.count
        self.count += 1
        v = self.count.to_bytes(8, 'big')
        self.f.write(v)
        self.f.seek(0)
        return c
