#!/usr/bin/python3
""" extract order data from the prospu state object
"""
import sys
import traceback
from datetime import datetime
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
from environment import DATA_DIR

def extract_args(argv):
    if len(argv) < 2:
        print('usage: {} <state-file>'.format(argv[0]))
        raise Exception("missing parms")
    return argv[1:]
    
def load_yaml(filename):
    with open(filename, 'r') as infile:
        return yaml.load(infile, Loader=Loader)    

def create_order_record(order):
    return {
        "id": order['id'],
        "exchange": order['exchange']['code'],
        "type": order['type'],
        "ticker": order['material']['ticker'],
        "count": order['initialAmount'],
        "amount": order['limit']['amount'],
        "currency": order['limit']['currency']
    }

def main(argv):
    """ runtime entrypoint """
    try:
        args = extract_args(argv)
        timestamp = datetime.now()
        state_file = load_yaml(args[0])

        records = []
        orders = state_file['comex']['trader']['orders']
        for key in orders['data']['data'].keys():
            order = orders['data']['data'][key]
            records.append(create_order_record(order))
        output = yaml.dump(records, Dumper=Dumper, explicit_start=True)
        print(output)
        return 0

    except Exception as err:
        traceback.print_exc()
        return 100

if __name__ == '__main__':
    sys.exit(main(sys.argv))