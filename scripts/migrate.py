#!/usr/bin/python
import os
import argparse
import logging

# external imports
import alembic
from alembic.config import Config as AlembicConfig
import confini
from xdg.BaseDirectory import (
        load_first_config,
    )

# local imports
from chainqueue.db import dsn_from_config

logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()

# BUG: the dbdir doesn't work after script install
rootdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
dbdir = os.path.join(rootdir, 'chainqueue', 'db')
migrationsdir = os.path.join(dbdir, 'migrations')

default_config_dir = load_first_config('chainqueue')
config_dir = os.environ.get('CONFINI_DIR', default_config_dir)

argparser = argparse.ArgumentParser()
argparser.add_argument('-c', type=str, default=config_dir, help='config file')
argparser.add_argument('--env-prefix', default=os.environ.get('CONFINI_ENV_PREFIX'), dest='env_prefix', type=str, help='environment prefix for variables to overwrite configuration')
argparser.add_argument('--migrations-dir', dest='migrations_dir', default=migrationsdir, type=str, help='path to alembic migrations directory')
argparser.add_argument('-v', action='store_true', help='be verbose')
argparser.add_argument('-vv', action='store_true', help='be more verbose')
args = argparser.parse_args()

if args.vv:
    logging.getLogger().setLevel(logging.DEBUG)
elif args.v:
    logging.getLogger().setLevel(logging.INFO)

config = confini.Config(args.c, args.env_prefix)
config.process()
config.censor('PASSWORD', 'DATABASE')
config.censor('PASSWORD', 'SSL')
logg.debug('config:\n{}'.format(config))

migrations_dir = os.path.join(args.migrations_dir, config.get('DATABASE_ENGINE'))
if not os.path.isdir(migrations_dir):
    logg.debug('migrations dir for engine {} not found, reverting to default'.format(config.get('DATABASE_ENGINE')))
    migrations_dir = os.path.join(args.migrations_dir, 'default')

# connect to database
dsn = dsn_from_config(config)


logg.info('using migrations dir {}'.format(migrations_dir))
logg.info('using db {}'.format(dsn))
ac = AlembicConfig(os.path.join(migrations_dir, 'alembic.ini'))
ac.set_main_option('sqlalchemy.url', dsn)
ac.set_main_option('script_location', migrations_dir)

alembic.command.upgrade(ac, 'head')
