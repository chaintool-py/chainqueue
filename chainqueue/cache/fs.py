# local imports
from .base import Cache


class FsCache(Cache):

    def __init__(self, path):
        self.path = path


