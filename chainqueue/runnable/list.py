# SPDX-License-Identifier: GPL-3.0-or-later

# standard imports
import os
import logging
import sys

# external imports
from hexathon import add_0x
import chainlib.cli
from chainlib.chain import ChainSpec

# local imports
from chainqueue.cli import Outputter


logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()

script_dir = os.path.dirname(os.path.realpath(__file__)) 
config_dir = os.path.join(script_dir, '..', 'data', 'config')

arg_flags = chainlib.cli.argflag_std_base | chainlib.cli.Flag.CHAIN_SPEC
argparser = chainlib.cli.ArgumentParser(arg_flags)
argparser.add_argument('--backend', type=str, default='sql', help='Backend to use (currently only "sql")')
argparser.add_argument('--start', type=str, help='Oldest transaction hash to include in results')
argparser.add_argument('--end', type=str, help='Newest transaction hash to include in results')
argparser.add_argument('--error', action='store_true', help='Only show transactions which have error state')
argparser.add_argument('--pending', action='store_true', help='Omit finalized transactions')
argparser.add_argument('--status-mask', type=int, dest='status_mask', help='Manually specify status bitmask value to match (overrides --error and --pending)')
argparser.add_argument('--summary', action='store_true', help='output summary for each status category')
argparser.add_argument('-o', '--column', dest='column', action='append', type=str, help='add a column to display')
argparser.add_positional('address', type=str, help='Ethereum address of recipient')
args = argparser.parse_args()
extra_args = {
    'address': None,
    'backend': None,
    'start': None,
    'end': None,
    'error': None,
    'pending': None,
    'status_mask': None,
    'column': None,
    'summary': None,
        }
config = chainlib.cli.Config.from_args(args, arg_flags, extra_args=extra_args, base_config_dir=config_dir)

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
session_method = None
if config.get('_BACKEND') == 'sql':
    from chainqueue.sql.query import get_account_tx as tx_lister
    from chainqueue.sql.query import get_tx_cache as tx_getter
    from chainqueue.runnable.sql import setup_backend
    from chainqueue.db.models.base import SessionBase
    setup_backend(config, debug=config.true('DATABASE_DEBUG'))
    session_method = SessionBase.create_session
else:
    raise NotImplementedError('backend {} not implemented'.format(config.get('_BACKEND')))

output_cols = config.get('_COLUMN')


def main():
    since = config.get('_START', None)
    if since != None:
        since = add_0x(since)
    until = config.get('_END', None)
    if until != None:
        until = add_0x(until)
    txs = tx_lister(chain_spec, config.get('_ADDRESS'), since=since, until=until, status=status_mask, not_status=not_status_mask)
    outputter = Outputter(chain_spec, sys.stdout, tx_getter, session_method=session_method, decode_status=config.true('_RAW'), cols=output_cols)
    if config.get('_SUMMARY'):
        for k in txs.keys():
            outputter.add(k)
        outputter.decode_summary()
    else:
        for k in txs.keys():
            outputter.decode_single(k)

if __name__ == '__main__':
    main()
