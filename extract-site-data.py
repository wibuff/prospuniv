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

def load_materials(platform):
    materials = {}
    for item in platform['reclaimableMaterials']:
        material = item['material']['ticker']
        materials[material] = item['amount']
    return materials 

def create_building(platform):
    ticker = platform['module']['reactorTicker']
    type = platform['module']['type']
    name = platform['module']['reactorName']
    area = platform['area']
    create_ts = platform['creationTime']['timestamp'] / 1000 # ts in ms
    create_dt = date.fromtimestamp(create_ts)
    materials = load_materials(platform)
    book_value = platform['bookValue']
    condition = platform['condition']

    return {
        'ticker': ticker,
        'type': type,
        'name': name, 
        'area': area,
        'created': create_dt,
        'reclaimable-materials': materials,
        'book-value': book_value,
        'condition': condition
    }

def main(argv):
    """ runtime entrypoint """
    try:
        args = extract_args(argv)
        timestamp = datetime.now()
        state_file = load_yaml(args[0])
        data = state_file['sites']['sites']['index']['data']

        sites = {}
        for key in data: 
            site = data[key]
            address = extract_address(site)
            platforms = site['platforms']
            
            buildings = []
            area_consumed = 0
            for platform in platforms:
                building = create_building(platform)
                area_consumed = area_consumed + building['area']
                buildings.append(building)

            area_total = site["area"]
            area_available = area_total - area_consumed

            sites[address['planet-name']] = {
                "id": key,
                "address": address,
                "buildings": buildings,
                "area": {
                    "available": area_available,
                    "consumed": area_consumed,
                    "total": area_total
                },
                'timestamp': timestamp
            }

        output = yaml.dump(sites, Dumper=Dumper, explicit_start=True)
        print(output)
        return 0

    except Exception:
        traceback.print_exc()
        return 100

if __name__ == '__main__':
    sys.exit(main(sys.argv))