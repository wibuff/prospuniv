#!/usr/bin/python3
""" model goals, analyzing resource, worker and space needs
"""
import sys
import traceback
import io
from datetime import datetime, date
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
from environment import DATA_DIR
from configuration import Buildings, Workers
from market import Market, Price
from inventory import Inventory
from report import Report

output = io.StringIO()
report = Report(output)

def extract_args(argv):
    if len(argv) < 5:
        print('usage: {} <goal-file> <site-file> <exchange-file> <base-exchange>'.format(argv[0]))
        sys.exit(1)
    return argv[1:]
    
def load_yaml(filename):
    with open(filename, 'r') as infile:
        return yaml.load(infile, Loader=Loader)    

WORKFORCE = ["PIONEER", "SETTLER", "TECHNICIAN", "ENGINEER", "SCIENTIST"]
WORKFORCE_HDR = list(map(lambda x: x[:3], WORKFORCE))

def format_building_workers(workers):
    workforce = [0,0,0,0,0]
    for worker in workers: 
        i = WORKFORCE.index(worker['type'])
        workforce[i] = workforce[i] + worker['count']
    return workforce 

def get_worker_consumption(site, demand):
    site_name = site['address']['planet-name']
    inventory = Inventory({})
    i = 0
    for worker_count in demand: 
        if worker_count > 0:
            worker_type = WORKFORCE[i]
            worker_spec = Workers[site_name][worker_type]
            for product in worker_spec['needs']:
                ticker = product['id']
                amount = float(worker_count)/product['basis'] * product['rate']
                inventory.add(ticker, amount)
        i = i + 1
    return inventory
        
def identify_worker_state(site):
    workforce = {
        'capacity': [0,0,0,0,0],
        'demand': [0,0,0,0,0],
    }
    for building in site['buildings']:
        ticker = building['ticker']
        if ticker in Buildings:
            building_data = Buildings[ticker]
            building_type = building_data['type'] 
            workers = format_building_workers(building_data['workers'])
            if building_type == "HABITATION":
                workforce['capacity'] = list(map(lambda x,y: x+y, workforce['capacity'], workers))
            else:
                workforce['demand'] = list(map(lambda x,y: x+y, workforce['demand'], workers))
    workforce['surplus'] = list(map(lambda x,y: x-y, workforce['capacity'], workforce['demand']))
    workforce['consumption'] = get_worker_consumption(site, workforce['demand'])
    return workforce

def calc_area(site):
    consumed = 0
    total = site['area']['total']
    for building in site['buildings']:
        consumed = consumed + building['area']
    available = total - consumed
    return {
        "available": available,
        "consumed": consumed,
        "total": total
    }

def create_building_summary(site): 
    buildings = {}
    for building in site['buildings']:
        ticker = building['ticker']
        if ticker in buildings:
            buildings[ticker] = buildings[ticker] + 1
        else:
            buildings[ticker] = 1

    fmt = "{}: {}"
    summary = []
    for ticker in buildings.keys():
        summary.append(fmt.format(ticker, buildings[ticker]))
    return ', '.join(summary)

def print_state(sites, exchange):
    for site_name in sites:
        site = sites[site_name]
        workforce = identify_worker_state(site)
        area = calc_area(site)

        site_desc = "Address   : Planet {0[planet-name]} ({0[planet-id]}) {0[system-name]} System ({0[system-id]})".format(site['address'])
        site_id =   "Site      : {}".format(site['id'][:8])
        area_desc = "Area      : {0[consumed]} / {0[available]} / {0[total]} (dev/avail/total)".format(area)
        bldg_desc = "Buildings : {}".format(create_building_summary(site))
        wf_hdr    = "Workers   : {0[0]:>6s}  {0[1]:>6s}  {0[2]:>6s}  {0[3]:>6s} {0[4]:>6s}".format(WORKFORCE_HDR)
        demand    = " Demand   :  {0[0]:>6d}  {0[1]:>6d}  {0[2]:>6d}  {0[3]:>6d} {0[4]:>6d}".format(workforce['demand'])
        capacity  = " Capacity :  {0[0]:>6d}  {0[1]:>6d}  {0[2]:>6d}  {0[3]:>6d} {0[4]:>6d}".format(workforce['capacity'])
        surplus   = " Surplus  :  {0[0]:>6d}  {0[1]:>6d}  {0[2]:>6d}  {0[3]:>6d} {0[4]:>6d}".format(workforce['surplus'])
        consumption = workforce['consumption'].summarize_inventory(exchange)

        report.major_break()
        report.output_general(site_desc)
        report.output_general(site_id)
        report.output_general(area_desc)
        report.output_general(bldg_desc)
        report.major_break()
        report.output_general(wf_hdr)
        report.output_general(demand)
        report.output_general(capacity)
        report.output_general(surplus)
        report.minor_break()
        report.output_value_table(consumption['inventory'], "Consumption/Day") 

def build(site, ticker, exchange):
    building_type = Buildings[ticker]
    building = {
        'area': building_type['area'],
        'condition': 100.0,
        'created': date.today(),
        'name': building_type['name'],
        'reclaimable-materials': building_type['materials'],
        'ticker': ticker,
        'type': building_type['type']
    }
    consumption = Inventory(building_type['materials'])
    summary = consumption.summarize_inventory(exchange)
    report.output_value_table(summary['inventory'], None) 
    site['buildings'].append(building)
    return consumption

def execute_actions(goal, sites, exchange):
    goal['consumption'] = Inventory({})
    for item in goal['actions']:
        action = item['action']
        site_name = item['site']
        ticker = item['id']
        site = sites[site_name]
        report.major_break()
        report.output_general('{} {} at {}'.format(action, ticker, site_name))
        if action == 'build': 
            consumption = build(site, ticker, exchange)
            goal['consumption'].add_all(consumption.items)
    return goal['consumption']

def execute_goals(goals, sites, exchange):
    total_consumption = Inventory({})
    for goal in goals['goals']: 
        print("")
        report.start()
        report.output_general('Goal: {}'.format(goal['description']))
        report.major_break()
        report.output_general("Notes:")

        notes = goal['notes'].split('\n')
        for note in notes: 
            if len(note) > 0:
                report.output_general(note)

        consumption = execute_actions(goal, sites, exchange)
        summary = consumption.summarize_inventory(exchange)
        total_consumption.add_all(consumption.items)

        report.major_break()
        report.output_value_table(summary['inventory'], "Goal Consumption Summary") 
        report.end()

        print("")
        report.start()
        report.output_general('Next State')
        print_state(sites, exchange)
        report.end()

    return total_consumption

def main(argv):
    """ runtime entrypoint """
    try:
        args = extract_args(argv)
        timestamp = datetime.now()
        print('*** model-goals ***')
        print('  model run time: {}'.format(timestamp))
        print('  goals file: {}'.format(args[0]))
        print('  site file: {}'.format(args[1]))
        print('  exchange file: {}'.format(args[2]))
        print('  exchange id: {}'.format(args[3]))

        goals = load_yaml(args[0])
        sites = load_yaml(args[1])
        exchange = Market(load_yaml(args[2]), args[3])

        report.start()
        report.output_general('Starting State')
        print_state(sites, exchange)
        report.end()

        consumption = execute_goals(goals, sites, exchange)
        report.newline()
        report.start()
        summary = consumption.summarize_inventory(exchange)
        report.output_value_table(summary['inventory'], "Consumption for all Goals") 
        report.end()
        report.newline()
        print(output.getvalue())
        return 0

    except Exception:
        traceback.print_exc()
        return 100

if __name__ == '__main__':
    sys.exit(main(sys.argv))