#!/usr/bin/python3
""" model the execution of a value stream
"""
import sys
import json
from inventory import Inventory
from clock import Duration
from valuestream import ValueStream
from configuration import load_datafile

def extract_args(argv):
    if len(argv) < 5:
        print('usage: %s <valstream-file> <inventory-init-file> <market-file> <run-time>' % argv[0])
        raise Exception("missing parms")
    return argv[1:]
    
def main(argv):
    """ runtime entrypoint """
    try:
        args = extract_args(argv)
        print("  valstream-file: {}".format(args[0]))
        print("  inventory-init-file: {}".format(args[1]))
        print("  market-file: {}".format(args[2]))
        print("  run-time: {}".format(args[3]))

        valstream = load_datafile(args[0])
        inventory = Inventory(load_datafile(args[1]))
        market = load_datafile(args[2])
        duration = Duration(args[3])
        valuestream = ValueStream(valstream, inventory, market, duration)
        valuestream.run()

    except Exception as err:
        print(err)
        return 100

if __name__ == '__main__':
    sys.exit(main(sys.argv))