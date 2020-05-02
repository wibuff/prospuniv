#!/usr/bin/python3
""" model the execution of a value stream
"""
import sys
import json
import traceback
from datetime import datetime
from inventory import Inventory
from market import Market
from clock import Duration
from valuestream import ValueStream
from configuration import load_datafile, load_yamlfile

def extract_args(argv):
    if len(argv) < 6:
        print('usage: %s <valstream-file> <inventory-init-file> <market-file> <exchange> <run-time>' % argv[0])
        raise Exception("missing parms")
    return argv[1:]
    
def main(argv):
    """ runtime entrypoint """
    try:
        args = extract_args(argv)
        timestamp = datetime.now()
        print('model value stream started {}'.format(timestamp))
        print('  valstream-file: {}'.format(args[0]))
        print('  inventory-init-file: {}'.format(args[1]))
        print('  market-file: {}'.format(args[2]))
        print('  exchange: {}'.format(args[3]))
        print('  run-time: {}'.format(args[4]))

        valstream = load_yamlfile(args[0])
        inventory = Inventory(load_yamlfile(args[1]))
        market = Market(load_yamlfile(args[2]), args[3])
        duration = Duration(args[4])
        valuestream = ValueStream(valstream, inventory, market, duration)
        valuestream.run()

    except Exception as err:
        traceback.print_exc()
        return 100

if __name__ == '__main__':
    sys.exit(main(sys.argv))