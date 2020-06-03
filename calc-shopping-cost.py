#!/usr/bin/python3
""" calc the cost of input shopping list
"""
import sys
from datetime import datetime
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
from environment import DATA_DIR
from inventory import Inventory
from market import Market

def extract_args(argv):
    if len(argv) < 4:
        print('usage: {} <list-file> <exchange-file> <outfile>'.format(argv[0]))
        raise Exception("missing parms")
    return argv[1:]
    
def load_yaml(filename):
    with open(filename, 'r') as infile:
        return yaml.load(infile, Loader=Loader)    

def main(argv):
    """ runtime entrypoint """
    try:
        args = extract_args(argv)
        inventory = Inventory(load_yaml(args[0]))
        exchanges = load_yaml(args[1])
        outfile = open(args[2], "w")

        ica_market = Market(exchanges, "IC1")
        ncc_market = Market(exchanges, "NC1")
        cis_market = Market(exchanges, "CI1")

        inventory.output_summary("List Cost (ICA)", ica_market, outfile)
        inventory.output_summary("List Cost (NCC)", ncc_market, outfile)
        inventory.output_summary("List Cost (CIS)", cis_market, outfile)

    except Exception as err:
        print(err)
        return 100

if __name__ == '__main__':
    sys.exit(main(sys.argv))