#!/usr/bin/python3
""" extract building data from the prospu state object
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

def load_materials(quantities):
    materials = {}
    for quantity in quantities:
        material = quantity['material']['ticker']
        materials[material] = quantity['amount']
    return materials 

HAB_CAPACITIES = {
    'HB1': [{ 'type': 'PIONEER', 'count': 100 }],
    'HB2': [{ 'type': 'SETTLER', 'count': 100 }],
    'HB3': [{ 'type': 'TECHNICIAN', 'count': 100 }],
    'HB4': [{ 'type': 'ENGINEER', 'count': 100 }],
    'HB5': [{ 'type': 'SCIENTIST', 'count': 100 }],
    'HBB': [{ 'type': 'PIONEER', 'count': 75 }, { 'type': 'SETTLER', 'count': 75 }],
    'HBC': [{ 'type': 'SETTLER', 'count': 75 }, { 'type': 'TECHNICIAN', 'count': 75 }],
    'HBM': [{ 'type': 'TECHNICIAN', 'count': 75 }, { 'type': 'ENGINEER', 'count': 75 }],
    'HBL': [{ 'type': 'ENGINEER', 'count': 75 }, { 'type': 'SCIENTIST', 'count': 75 }]
}

def load_workers(capacities, ticker):
    if ticker in HAB_CAPACITIES:
        return HAB_CAPACITIES[ticker]

    workers = []
    for cap in capacities:
        worker = {
            'type': cap['level'],
            'count': cap['capacity']
        }
        workers.append(worker)
    return workers 

def create_building(option):
    ticker = option['ticker']
    workers = load_workers(option['workforceCapacities'], ticker)
    materials = load_materials(option['materials']['quantities'])
    return {
        'ticker': ticker,
        'type': option['type'],
        'name': option['name'],
        'area': option['area'],
        'expertise': option['expertiseCategory'],
        'workers': workers,
        'materials': materials
    }

def main(argv):
    """ runtime entrypoint """
    try:
        args = extract_args(argv)
        timestamp = datetime.now()
        state_file = load_yaml(args[0])
        sites = state_file['sites']['sites']['index']['data']

        buildings = {}
        # TODO handle multiple sites - assume materials costs different by site
        for key in sites: 
            build_options = sites[key]['buildOptions']['options']
            for option in build_options:
                buildings[option['ticker']] = create_building(option)
        
        output = yaml.dump(buildings, Dumper=Dumper, explicit_start=True)
        print(output)

    except Exception as err:
        print(err)
        return 100

if __name__ == '__main__':
    sys.exit(main(sys.argv))