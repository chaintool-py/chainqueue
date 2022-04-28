# external imports
from chainlib.settings import ChainSettings


class ChainqueueSettings(ChainSettings):

    def process_queue_backend(self, config):
        self.o['QUEUE_BACKEND'] = config.get('QUEUE_BACKEND')
