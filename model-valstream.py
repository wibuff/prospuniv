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
    if len(argv) < 3:
        #print('usage: %s <valstream-file> <inventory-init-file> <market-file> <exchange> <run-time>' % argv[0])
        print('usage: %s <run-file> <date>' % argv[0])
        sys.exit(1)
    return argv[1:]

def load_config(args, timestamp):
    config_file = load_yamlfile(args[0])
    config_date = args[1]

    description = config_file['description']
    valstream_file = config_file['valstream']
    inventory_file = config_file['inventory']
    exchange_file = config_file['exchange']
    currency = config_file['currency']
    duration_config = config_file['duration']
    output_file = config_file['output']

    if '{date}' in inventory_file:
        inventory_file = inventory_file.replace('{date}', config_date)
    if '{date}' in exchange_file:
        exchange_file = exchange_file.replace('{date}', config_date)

    print('model value stream started {}'.format(timestamp))
    print('  description : {}'.format(description))
    print('  config date : {}'.format(config_date))
    print('  valstream   : {}'.format(valstream_file))
    print('  inventory   : {}'.format(inventory_file))
    print('  exchange    : {}'.format(exchange_file))
    print('  currency    : {}'.format(currency))
    print('  run-time    : {}'.format(duration_config))

    valstream = load_yamlfile(valstream_file)
    inventory = Inventory(load_yamlfile(inventory_file))
    market = Market(load_yamlfile(exchange_file), currency)
    duration = Duration(duration_config)

    return {
        'config-date': config_date,
        'valstream': valstream,
        'inventory': inventory,
        'market': market,
        'duration': duration,
        'output': output_file
    }

def main(argv):
    """ runtime entrypoint """
    try:
        args = extract_args(argv)
        timestamp = datetime.now()
        config = load_config(args, timestamp)
        valuestream = ValueStream(config)
        valuestream.run()

    except Exception:
        traceback.print_exc()
        return 100

if __name__ == '__main__':
    sys.exit(main(sys.argv))