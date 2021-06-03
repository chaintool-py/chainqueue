#!/usr/bin/python
import os
import argparse
import logging

# external imports
import alembic
from alembic.config import Config as AlembicConfig
import confini
from xdg.BaseDirectory import (
        xdg_data_dirs,
        load_first_config,
    )

# local imports
from chainqueue.db import dsn_from_config

logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()

rootdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
dbdir = os.path.join(rootdir, 'chainqueue', 'db')
default_migrations_dir = os.path.join(dbdir, 'migrations')
default_data_dir = os.path.join(xdg_data_dirs[0], 'chainqueue')

default_config_dir = load_first_config('chainqueue')
config_dir = os.environ.get('CONFINI_DIR', default_config_dir)

argparser = argparse.ArgumentParser()
argparser.add_argument('-c', type=str, default=config_dir, help='config file')
argparser.add_argument('--env-prefix', default=os.environ.get('CONFINI_ENV_PREFIX'), dest='env_prefix', type=str, help='environment prefix for variables to overwrite configuration')
argparser.add_argument('--data-dir', dest='data_dir', type=str, default=default_data_dir, help='data directory')
argparser.add_argument('--migrations-dir', dest='migrations_dir', default=default_migrations_dir, type=str, help='path to alembic migrations directory')
argparser.add_argument('--reset', action='store_true', help='reset exsting database')
argparser.add_argument('-v', action='store_true', help='be verbose')
argparser.add_argument('-vv', action='store_true', help='be more verbose')
args = argparser.parse_args()

if args.vv:
    logging.getLogger().setLevel(logging.DEBUG)
elif args.v:
    logging.getLogger().setLevel(logging.INFO)

# process config
config = confini.Config(args.c, args.env_prefix)
config.process()
args_override = {
            'PATH_DATA': getattr(args, 'data_dir'),
        }
config.dict_override(args_override, 'cli args')

if config.get('DATABASE_ENGINE') == 'sqlite':
    config.add(os.path.join(config.get('PATH_DATA'), config.get('DATABASE_NAME')), 'DATABASE_NAME', True)
 
config.censor('PASSWORD', 'DATABASE')

config.add(os.path.join(args.migrations_dir, config.get('DATABASE_ENGINE')), '_MIGRATIONS_DIR', True)
if not os.path.isdir(config.get('_MIGRATIONS_DIR')):
    logg.debug('migrations dir for engine {} not found, reverting to default'.format(config.get('DATABASE_ENGINE')))
    config.add(os.path.join(args.migrations_dir, 'default'), '_MIGRATIONS_DIR', True)
logg.debug('config loaded:\n{}'.format(config))

os.makedirs(config.get('PATH_DATA'), exist_ok=True)

dsn = dsn_from_config(config)

def main():
    logg.info('using migrations dir {}'.format(config.get('_MIGRATIONS_DIR')))
    logg.info('using db {}'.format(dsn))
    ac = AlembicConfig(os.path.join(config.get('_MIGRATIONS_DIR'), 'alembic.ini'))
    ac.set_main_option('sqlalchemy.url', dsn)
    ac.set_main_option('script_location', config.get('_MIGRATIONS_DIR'))

    if args.reset:
        logg.debug('reset is set, purging existing content')
        alembic.command.downgrade(ac, 'base')

    alembic.command.upgrade(ac, 'head')

if __name__ == '__main__':
    main()
