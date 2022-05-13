# standard imports
import os
import logging

# external imports
from chainlib.settings import ChainSettings
from chainqueue.state import Status
from chainqueue.store import Store

logg = logging.getLogger(__name__)


def process_queue_tx(settings, config):
    settings.set('TX_DIGEST_SIZE', config.get('TX_DIGEST_SIZE'))
    return settings


def process_queue_backend(settings, config):
    settings.set('QUEUE_BACKEND', config.get('QUEUE_BACKEND'))
    return settings


def process_queue_store(settings, config):
    status = Status(settings.o['QUEUE_STORE_FACTORY'], allow_invalid=True)
    settings.set('QUEUE_STATE_STORE'], status)
    store = Store(
        settings.o['CHAIN_SPEC'],
        settings.o['QUEUE_STATE_STORE'],
        settings.o['QUEUE_INDEX_STORE'],
        settings.o['QUEUE_COUNTER_STORE'],
        sync=True,
        )
    settings.set('QUEUE_STORE', store)
    return settings


def process_queue_paths(settings, config):
    index_dir = config.get('QUEUE_INDEX_PATH')
    if index_dir == None:
        index_dir = os.path.join(config.get('QUEUE_STATE_PATH'), 'tx')

    counter_dir = config.get('QUEUE_COUNTER_PATH')
    if counter_dir == None:
        counter_dir = os.path.join(config.get('QUEUE_STATE_PATH'))

    settings.set('QUEUE_STATE_PATH', config.get('QUEUE_STATE_PATH'))
    settings.set('QUEUE_INDEX_PATH', index_dir)
    settings.set('QUEUE_COUNTER_PATH'], counter_dir)
    return settings


def process_queue_backend_fs(settings, config):
    from chainqueue.store.fs import IndexStore
    from chainqueue.store.fs import CounterStore
    from shep.store.file import SimpleFileStoreFactory
    index_store = IndexStore(settings.o['QUEUE_INDEX_PATH'], digest_bytes=int(settings.o['TX_DIGEST_SIZE']))
    counter_store = CounterStore(settings.o['QUEUE_COUNTER_PATH'])
    factory = SimpleFileStoreFactory(settings.o['QUEUE_STATE_PATH'], use_lock=True).add

    settings.set('QUEUE_INDEX_STORE', index_store)
    settings.set('QUEUE_COUNTER_STORE', counter_store)
    settings.set('QUEUE_STORE_FACTORY', factory)

    return settings


def process_queue_status_filter(settings, config):
    states = 0
    store = settings.get('QUEUE_STATE_STORE')
    if len(config.get('_STATUS_MASK')) == 0:
        for v in store.all(numeric=True):
            states |= v
        logg.debug('state store {}'.format(states))
    else:
        for v in config.get('_STATUS_MASK'):
            try:
                states |= int(v)
                continue
            except ValueError:
                pass
            
            state = store.from_name(v)
            logg.debug('resolved state argument {} to numeric state {}'.format(v, state))
            states |= state

    settings.set('QUEUE_STATUS_FILTER', states)
    return settings


def process_queue(settings, config):
    settings = process_queue_tx(settings, config)
    settings = process_queue_paths(settings, config)
    if config.get('QUEUE_BACKEND') == 'fs':
        settings = process_queue_backend_fs(settings, config)
    settings = process_queue_backend(settings, config)
    settings = process_queue_store(settings, config)
    settings = process_queue_status_filter(settings, config)
    return settings


def process_settings(settings, config):
    super(ChainqueueSettings, settings).process(config)
    settings = settings.process_queue(settings, config) 
    return settings
