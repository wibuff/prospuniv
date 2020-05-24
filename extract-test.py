#!/usr/bin/python3
""" extract site data from the prospu state object
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
        raise Exception("missing parms")
    return argv[1:]
    
def load_yaml(filename):
    with open(filename, 'r') as infile:
        return yaml.load(infile, Loader=Loader)    

def main(argv):
    """ runtime entrypoint """
    try:
        args = extract_args(argv)
        state_file = load_yaml(args[0])

        sites = state_file['sites']
        output = yaml.dump(sites, Dumper=Dumper, explicit_start=True)
        with open('logs/sites.yaml', 'w') as sitefile:
            print(output, file=sitefile)

        prod = state_file['production']
        output = yaml.dump(prod, Dumper=Dumper, explicit_start=True)
        with open('logs/production.yaml', 'w') as prodfile:
            print(output, file=prodfile)

        return 0

    except Exception:
        traceback.print_exc()
        return 100

if __name__ == '__main__':
    sys.exit(main(sys.argv))