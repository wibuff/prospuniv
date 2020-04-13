#!/usr/bin/python3
""" extract worker data from the prospu state object
"""
import sys
from datetime import datetime
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
from environment import DATA_DIR

def extract_args(argv):
    if len(argv) < 2:
        print('usage: {} <state-file>',format(argv[0]))
        raise Exception("missing parms")
    return argv[1:]
    
def load_yaml(filename):
    with open(filename, 'r') as infile:
        return yaml.load(infile, Loader=Loader)    

def create_worker(workforce):
    needs = workforce['needs']
    essentials = []
    non_essentials = []

    for need in needs:
        id = need['material']['ticker']
        units_per_100 = need['unitsPer100']
        essential = need['essential']
        material = {
            "id": id,
            "rate": float(units_per_100),
            "basis": 100.0
        }
        if essential: 
            essentials.append(material)
        else: 
            non_essentials.append(material)

    # TODO address hard-coded efficiency, if needed
    return {
        "efficiency": 0.79,
        "essentials": essentials,
        "non-essentials": non_essentials
    }

def main(argv):
    """ runtime entrypoint """
    try:
        args = extract_args(argv)
        timestamp = datetime.now()
        state_file = load_yaml(args[0])
        sites = state_file['workforce']['workforces']['data']

        workers = {}
        # TODO handle multiple sites - TBD site differences for workers
        for key in sites: 
            workforces = sites[key]['workforces']
            for workforce in workforces:
                workers[workforce['level']] = create_worker(workforce)
        
        output = yaml.dump(workers, Dumper=Dumper, explicit_start=True)
        print(output)

    except Exception as err:
        print(err)
        return 100

if __name__ == '__main__':
    sys.exit(main(sys.argv))