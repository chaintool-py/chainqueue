# SPDX-License-Identifier: GPL-3.0-or-later

# standard imports
import os
import logging
import argparse

# local imports
from chainqueue.state import Status

argparser = argparse.ArgumentParser()
argparser.add_argument('-r', '--raw', dest='r', action='store_true', help='Always print pure state element strings')
argparser.add_argument('state', type=str, help='State to interpret')
args = argparser.parse_args()

status_interpreter = Status(None, allow_invalid=True)


def handle_numeric(v, elements=False):
    if elements:
        if not status_interpreter.is_pure(v):
            return status_interpreter.elements(v)
    return status_interpreter.name(v)


def handle_string(v):
    try:
        return status_interpreter.from_name(v)
    except AttributeError:
        return status_interpreter.from_elements(v)


def main():
    v = None
    numeric = False
    try:
        v = int(args.state)
        numeric = True
    except:
        v = args.state
      
    r = None
    if numeric:
        r = handle_numeric(v, elements=args.r)
    else:
        r = handle_string(v)

    print(r)

if __name__ == '__main__':
    main()
