# standard imports
import stat
import logging
import os

# local imports
from chainqueue.enum import (
        StatusBits,
        status_bytes,
        )

logg = logging.getLogger(__name__)


class FsQueueBackend:

    
    def add(self, label, content, prefix):
        raise NotImplementedError()


    def get_index(self, idx):
        raise NotImplementedError()


    def set_prefix(self, idx, prefix):
        raise NotImplementedError()


class FsQueue:

    def __init__(self, root_path, backend=FsQueueBackend()):
        self.backend = backend
        self.path = root_path
        self.path_state = {}
        
        try:
            fi = os.stat(self.path)
            self.__verify_directory()
        except FileNotFoundError:
            FsQueue.__prepare_directory(self.path)

        for r in FsQueue.__state_dirs(self.path):
            self.path_state[r[0]] = r[1]

        self.index_path = os.path.join(self.path, '.active')
        os.makedirs(self.index_path, exist_ok=True)


    def add(self, key, value):
        prefix = status_bytes()
        c = self.backend.add(key, value, prefix=prefix)

        key_hex = key.hex()
        entry_path = os.path.join(self.index_path, key_hex)
        f = open(entry_path, 'xb')
        f.write(c.to_bytes(8, byteorder='big'))
        f.close()

        ptr_path = os.path.join(self.path_state['new'], key_hex)
        os.link(entry_path, ptr_path)

        logg.debug('added new queue entry {} -> {} index {}'.format(ptr_path, entry_path, c))


    @staticmethod
    def __state_dirs(path):
        r = []
        for s in [
                'new',
                'reserved',
                'ready',
                'error',
                'defer',
                ]:
            r.append((s, os.path.join(path, 'spool', s)))
        return r


    def __verify_directory(self):
        return True


    @staticmethod
    def __prepare_directory(path):
        os.makedirs(path, exist_ok=True)
        os.makedirs(os.path.join(path, '.cache'))
        for r in FsQueue.__state_dirs(path):
            os.makedirs(r[1])
