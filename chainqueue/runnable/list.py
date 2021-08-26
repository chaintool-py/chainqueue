# SPDX-License-Identifier: GPL-3.0-or-later

# standard imports
import os
import logging
import sys

# external imports
from hexathon import add_0x
import chainlib.cli
from chainlib.chain import ChainSpec
from crypto_dev_signer.eth.signer import ReferenceSigner as EIP155Signer

# local imports
from chainqueue.enum import (
        StatusBits,
        all_errors,
        is_alive,
        is_error_status,
        status_str,
        )


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


class Outputter:

    def __init__(self, chain_spec, writer, session_method=None):
        self.writer = writer
        self.chain_spec = chain_spec
        self.chain_spec_str = str(chain_spec)
        self.session = None
        if session_method != None:
            self.session = session_method()
        self.results = {
            'pending_error': 0,
            'final_error': 0,
            'pending': 0,
            'final': 0,
                }

    def __del__(self):
        if self.session != None:
            self.session.close()


    def add(self, tx_hash):
        tx = tx_getter(self.chain_spec, tx_hash, session=self.session)
        category = None
        if is_alive(tx['status_code']):
            category = 'pending'
        else:
            category = 'final'
        self.results[category] += 1
        if is_error_status(tx['status_code']):
            logg.debug('registered {} as {} with error'.format(tx_hash, category))
            self.results[category + '_error'] += 1
        else:
            logg.debug('registered {} as {}'.format(tx_hash, category))
     

    def decode_summary(self):
        self.writer.write('pending\t{}\t{}\n'.format(self.results['pending'], self.results['pending_error']))
        self.writer.write('final\t{}\t{}\n'.format(self.results['final'], self.results['final_error']))
        self.writer.write('total\t{}\t{}\n'.format(self.results['final'] + self.results['pending'], self.results['final_error'] + self.results['pending_error']))


    def decode_single(self, tx_hash):
        tx = tx_getter(self.chain_spec, tx_hash, session=self.session)
        status = tx['status']
        if config.get('_RAW'):
            status = status_str(tx['status_code'], bits_only=True)
        self.writer.write('{}\t{}\t{}\t{}\n'.format(self.chain_spec_str, add_0x(tx_hash), status, tx['status_code']))


def main():
    since = config.get('_START', None)
    if since != None:
        since = add_0x(since)
    until = config.get('_END', None)
    if until != None:
        until = add_0x(until)
    txs = tx_lister(chain_spec, config.get('_ADDRESS'), since=since, until=until, status=status_mask, not_status=not_status_mask)
    outputter = Outputter(chain_spec, sys.stdout, session_method=session_method)
    if config.get('_SUMMARY'):
        for k in txs.keys():
            outputter.add(k)
        outputter.decode_summary()
    else:
        for k in txs.keys():
            outputter.decode_single(k)

if __name__ == '__main__':
    main()
