# standard imports
import os
import logging

# external imports
from chainlib.settings import ChainSettings
from chainqueue.state import Status
from chainqueue.store import Store

logg = logging.getLogger(__name__)


class ChainqueueSettings(ChainSettings):

    def process_queue_tx(self, config):
        self.o['TX_DIGEST_SIZE'] = config.get('TX_DIGEST_SIZE')


    def process_queue_backend(self, config):
        self.o['QUEUE_BACKEND'] = config.get('QUEUE_BACKEND')
        self.o['QUEUE_STATE_STORE'] = Status(self.o['QUEUE_STORE_FACTORY'], allow_invalid=True)
        self.o['QUEUE_STORE'] = Store(
            self.o['CHAIN_SPEC'],
            self.o['QUEUE_STATE_STORE'],
            self.o['QUEUE_INDEX_STORE'],
            self.o['QUEUE_COUNTER_STORE'],
            sync=True,
            )


    def process_queue_paths(self, config):
        index_dir = config.get('QUEUE_INDEX_PATH')
        if index_dir == None:
            index_dir = os.path.join(config.get('QUEUE_STATE_PATH'), 'tx')

        counter_dir = config.get('QUEUE_COUNTER_PATH')
        if counter_dir == None:
            counter_dir = os.path.join(config.get('QUEUE_STATE_PATH'))

        self.o['QUEUE_STATE_PATH'] = config.get('QUEUE_STATE_PATH')
        self.o['QUEUE_INDEX_PATH'] = index_dir
        self.o['QUEUE_COUNTER_PATH'] = counter_dir


    def process_queue_backend_fs(self, config):
        from chainqueue.store.fs import IndexStore
        from chainqueue.store.fs import CounterStore
        from shep.store.file import SimpleFileStoreFactory
        index_store = IndexStore(self.o['QUEUE_INDEX_PATH'], digest_bytes=self.o['TX_DIGEST_SIZE'])
        counter_store = CounterStore(self.o['QUEUE_COUNTER_PATH'])
        factory = SimpleFileStoreFactory(self.o['QUEUE_STATE_PATH'], use_lock=True).add

        self.o['QUEUE_INDEX_STORE'] = index_store
        self.o['QUEUE_COUNTER_STORE'] = counter_store
        self.o['QUEUE_STORE_FACTORY'] = factory


    def process_queue_status_filter(self, config):
        states = 0
        if len(config.get('_STATUS_MASK')) == 0:
            for v in self.o['QUEUE_STATE_STORE'].all(numeric=True):
                states |= v
            logg.debug('state store {}'.format(states))
        else:
            for v in config.get('_STATUS_MASK'):
                try:
                    states |= int(v)
                    continue
                except ValueError:
                    pass
                
                state = self.o['QUEUE_STATE_STORE'].from_name(v)
                logg.debug('resolved state argument {} to numeric state {}'.format(v, state))
                states |= state

        self.o['QUEUE_STATUS_FILTER'] = states


    def process(self, config):
        super(ChainqueueSettings, self).process(config)
        self.process_queue_tx(config)
        self.process_queue_paths(config)
        if config.get('_BACKEND') == 'fs':
            self.process_queue_backend_fs(config)
        self.process_queue_backend(config)
        self.process_queue_status_filter(config)
