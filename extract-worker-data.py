#!/usr/bin/python3
""" extract worker data from the prospu state object
"""
import sys
from datetime import datetime
import traceback
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
from environment import DATA_DIR

def extract_args(argv):
    if len(argv) < 2:
        print('usage: {} <state-file>',format(argv[0]))
        sys.exit(1)
    return argv[1:]
    
def load_yaml(filename):
    with open(filename, 'r') as infile:
        return yaml.load(infile, Loader=Loader)    

def create_worker(workforce):
    needs = workforce['needs']
    materials = []

    for need in needs:
        id = need['material']['ticker']
        units_per_100 = need['unitsPer100']
        essential = need['essential']
        material = {
            "id": id,
            "rate": float(units_per_100),
            "basis": 100.0,
            'essential': essential
        }
        materials.append(material)

    # TODO address hard-coded efficiency, if needed
    return {
        "efficiency": 0.79,
        "needs": materials
    }

def extract_address(location):
    address = {}
    for line in location['address']['lines']:
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
        workforce_data = state_file['workforce']['workforces']['data']

        workers = {}
        # TODO handle multiple sites - TBD site differences for workers
        for key in workforce_data: 
            location = workforce_data[key]
            address = extract_address(location)
            planet = address['planet-name']
            workers[planet] = {
                'id': key,
                'address': address,
            }
            loc_workforces = location['workforces']
            for workforce in loc_workforces:
                workers[planet][workforce['level']] = create_worker(workforce)
        
        output = yaml.dump(workers, Dumper=Dumper, explicit_start=True)
        print(output)

    except Exception:
        traceback.print_exc()
        return 100

if __name__ == '__main__':
    sys.exit(main(sys.argv))