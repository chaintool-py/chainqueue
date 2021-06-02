import syslog
import sys
import time
import socket
import signal
import os
import logging
import stat
import argparse
import uuid

# external imports
import confini
from xdg.BaseDirectory import (
        load_first_config,
        get_runtime_dir,
        )
from hexathon import strip_0x
from chainlib.chain import ChainSpec

# local imports
from chainqueue.sql.backend import SQLBackend
from chainqueue.db import dsn_from_config
from chainqueue.adapters.eth import EthAdapter

logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()

default_config_dir = load_first_config('chainqueue')
config_dir = os.environ.get('CONFINI_DIR', default_config_dir)

runtime_dir = os.path.join(get_runtime_dir(), 'chainqueue')

argparser = argparse.ArgumentParser('chainqueue transaction submission and trigger server')
argparser.add_argument('-c', '--config', dest='c', type=str, default=config_dir, help='configuration directory')
argparser.add_argument('--runtime-dir', dest='runtime_dir', type=str, default=runtime_dir, help='runtime directory')
argparser.add_argument('--session-id', dest='session_id', type=str, default=str(uuid.uuid4()), help='session id to use for session')
argparser.add_argument('-v', action='store_true', help='be verbose')
argparser.add_argument('-vv', action='store_true', help='be very verbose')
args = argparser.parse_args(sys.argv[1:])

if args.vv:
    logg.setLevel(logging.DEBUG)
elif args.v:
    logg.setLevel(logging.INFO)

config = confini.Config(args.c)
config.process()
args_override = {
            'SESSION_RUNTIME_DIR': getattr(args, 'runtime_dir'),
        }
config.dict_override(args_override, 'cli args')
config.add(getattr(args, 'session_id'), '_SESSION_ID', True)

if not config.get('SESSION_SOCKET_PATH'):
    socket_path = os.path.join(config.get('SESSION_RUNTIME_DIR'), config.get('_SESSION_ID'), 'chainqueue.sock')
    config.add(socket_path, 'SESSION_SOCKET_PATH', True)
logg.debug('config loaded:\n{}'.format(config))


class SessionController:

    def __init__(self, config):
        self.dead = False
        os.makedirs(os.path.dirname(config.get('SESSION_SOCKET_PATH')), exist_ok=True)
        try:
            os.unlink(config.get('SESSION_SOCKET_PATH'))
        except FileNotFoundError:
            pass

        self.srv = socket.socket(family=socket.AF_UNIX, type=socket.SOCK_STREAM)
        self.srv.bind(config.get('SESSION_SOCKET_PATH'))
        self.srv.listen(2)
        self.srv.settimeout(5.0)

    def shutdown(self, signo, frame):
        if self.dead:
            return
        self.dead = True
        if signo != None:
            syslog.syslog('closing on {}'.format(signo))
        else:
            syslog.syslog('explicit shutdown')
        sockname = self.srv.getsockname()
        self.srv.close()
        try:
            os.unlink(sockname)
        except FileNotFoundError:
            logg.warning('socket file {} already gone'.format(sockname))


    def get_connection(self):
        return self.srv.accept()


ctrl = SessionController(config)

signal.signal(signal.SIGINT, ctrl.shutdown)
signal.signal(signal.SIGTERM, ctrl.shutdown)

dsn = dsn_from_config(config)
backend = SQLBackend(dsn)
adapter = EthAdapter(backend)
chain_spec = ChainSpec.from_chain_str('evm:mainnet:1')

if __name__ == '__main__':
    while True:
        srvs = None
        try:
            (srvs, srvs_addr) = ctrl.get_connection()
        except OSError as e:
            try:
                fi = os.stat(config.get('SESSION_SOCKET_PATH'))
            except FileNotFoundError:
                logg.error('socket is gone')
                break
            if not stat.S_ISSOCK(fi.st_mode):
                logg.error('entity on socket path is not a socket')
                break
            if srvs == None:
                logg.debug('ping')
                continue
        srvs.setblocking(False)
        data_in = srvs.recv(1024)
        data_in_str = data_in.decode('utf-8')
        data = bytes.fromhex(strip_0x(data_in_str))
        r = adapter.add(chain_spec, data)
        srvs.send(r.to_bytes(4, byteorder='big'))

    ctrl.shutdown(None, None)
