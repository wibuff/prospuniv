#!/usr/bin/python3
""" extract inventory data from the prospu state object
"""
import sys
import traceback
from datetime import datetime, date
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
from environment import DATA_DIR

def extract_args(argv):
    if len(argv) < 2:
        print('usage: {} <state-file>'.format(argv[0]))
        sys.exit(1)
    return argv[1:]
    
def load_yaml(filename):
    with open(filename, 'r') as infile:
        return yaml.load(infile, Loader=Loader)    

def extract_address(site):
    address = {}
    for line in site['address']['lines']:
        name = line['entity']['name']
        id = line['entity']['naturalId']
        if line['type'] == "PLANET":
            address['planet-name'] = name
            address['planet-id'] = id
        elif line['type'] == "SYSTEM":
            address['system-name'] = name
            address['system-id'] = id
    return address

def main(argv):
    """ runtime entrypoint """
    try:
        args = extract_args(argv)
        state_file = load_yaml(args[0])
        stores = state_file['storage']['stores']

        inventory = {}
        # TODO update to handle multiples sites/bases
        for store_id in stores: 
            store = stores[store_id]
            if store['type'] == 'STORE':
                for item in store['items']:
                    ticker = item['quantity']['material']['ticker']
                    amount = item['quantity']['amount']
                    if ticker in inventory: 
                        inventory[ticker] = inventory[ticker] + amount
                    else: 
                        inventory[ticker] = amount

        output = yaml.dump(inventory, Dumper=Dumper, explicit_start=True)
        print(output)
        return 0

    except Exception:
        traceback.print_exc()
        return 100

if __name__ == '__main__':
    sys.exit(main(sys.argv))