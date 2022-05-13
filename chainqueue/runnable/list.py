# SPDX-License-Identifier: GPL-3.0-or-later

# standard imports
import os
import logging
import sys
import importlib

# external imports
from hexathon import add_0x
import chainlib.cli
from chainlib.chain import ChainSpec

# local imports
import chainqueue.cli
#from chainqueue.cli.output import Outputter
from chainqueue.settings import ChainqueueSettings
from chainqueue.store import Store
from chainqueue.entry import QueueEntry


logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()

script_dir = os.path.dirname(os.path.realpath(__file__)) 
config_dir = os.path.join(script_dir, '..', 'data', 'config')

arg_flags = chainlib.cli.argflag_std_base | chainlib.cli.Flag.CHAIN_SPEC | chainlib.cli.Flag.UNSAFE
argparser = chainlib.cli.ArgumentParser(arg_flags)
argparser.add_argument('--backend', type=str, default='sql', help='Backend to use')
argparser.add_argument('--error', action='store_true', help='Only show transactions which have error state')
argparser.add_argument('--no-final', action='store_true', dest='no_final', help='Omit finalized transactions')
argparser.add_argument('--status-mask', type=str, dest='status_mask', action='append', default=[], help='Manually specify status bitmask value to match (overrides --error and --pending)')
argparser.add_argument('--exact', action='store_true', help='Match status exact')
argparser.add_argument('--include-pending', action='store_true', dest='include_pending', help='Include transactions in unprocessed state (pending)')
argparser.add_argument('--renderer', type=str, default=[], action='append', help='Transaction renderer for output')
argparser.add_positional('address', required=False, type=str, help='Ethereum address of recipient')
args = argparser.parse_args()
extra_args = {
    'address': None,
    'backend': None,
    'state_dir': None,
    'exact': None,
    'error': None,
    'include_pending': '_PENDING',
    'status_mask': None,
    'no_final': None,
    'renderer': None,
        }
config = chainlib.cli.Config.from_args(args, arg_flags, extra_args=extra_args, base_config_dir=config_dir)
config = chainqueue.cli.config.process_config(config, args, 0)
logg.debug('config loaded:\n{}'.format(config))

chain_spec = ChainSpec.from_chain_str(config.get('CHAIN_SPEC'))

status_mask = config.get('_STATUS_MASK', None)
not_status_mask = None
if status_mask == None:
    if config.get('_ERROR'):
        status_mask = all_errors()
    if config.get('_PENDING'):
        not_status_mask = StatusBits.FINAL

tx_getter = None
tx_lister = None
#output_cols = config.get('_COLUMN')

renderers_mods = []
for renderer in config.get('_RENDERER'):
    m = importlib.import_module(renderer)
    renderers_mods.append(m)
    logg.info('using renderer module {}'.format(renderer))

settings = ChainqueueSettings()
settings.process(config)
logg.debug('settings:\n{}'.format(settings))


def main():
#    since = config.get('_START', None)
#    if since != None:
#        since = add_0x(since)
#    until = config.get('_END', None)
#    if until != None:
#        until = add_0x(until)
#    txs = tx_lister(chain_spec, config.get('_ADDRESS'), since=since, until=until, status=status_mask, not_status=not_status_mask)
    txs = settings.get('QUEUE_STORE').by_state(state=settings.get('QUEUE_STATUS_FILTER'), strict=config.get('_EXACT'), include_pending=config.get('_PENDING'))
    
    for i, tx_hash in enumerate(txs):
        entry = QueueEntry(settings.get('QUEUE_STORE'), tx_hash)
        entry.load()
        v = None
        if len(renderers_mods) == 0:
            v = str(entry)
        else:
            for m in renderers_mods:
                v = m.apply(i, settings, v, settings.get('CHAIN_SPEC'), entry)
        print(v)


if __name__ == '__main__':
    main()
