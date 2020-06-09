#!/usr/bin/python3
""" build-graph.py
Creates multiple graphs representing production trees made up of multiple production template 
combinations. Graphs are indexed by template id and output to files in multiple formats:
JSON and YAML.
"""
import sys
import json
import traceback
import copy
from datetime import datetime
from inventory import Inventory
from market import Market
from clock import Duration
from valuestream import ValueStream
from configuration import load_datafile, load_yamlfile
from graphnode import GraphNode
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

def extract_args(argv):
    if len(argv) < 3:
        print('usage: {} <run-file> <date>'.format(argv[0]))
        sys.exit(1)
    return argv[1:]

"""  Load update the configuration object from the file
"""
def load_config(args, timestamp):
    config_file = load_yamlfile(args[0])
    config_date = args[1]

    # update config-date specific fields
    for key in config_file.keys():
        field = config_file[key]
        if '{date}' in field:
            config_file[key] = field.replace('{date}', config_date)

    description = config_file['description']
    template_file = config_file['templates']
    building_file = config_file['buildings']
    efficiency_file = config_file['efficiency']
    worker_file = config_file['workers']
    exchange_file = config_file['exchange']
    currency = config_file['currency']
    csv_out_file = config_file['output-csv']
    logfile = config_file['logfile']

    csvout = open(csv_out_file, 'w')
    logout = open(logfile, 'w')

    print('model value stream started {}'.format(timestamp))
    print('  description    : {}'.format(description))
    print('  config date    : {}'.format(config_date))
    print('  templates      : {}'.format(template_file))
    print('  buildings      : {}'.format(building_file))
    print('  efficiency     : {}'.format(efficiency_file))
    print('  workers        : {}'.format(worker_file))
    print('  exchange       : {}'.format(exchange_file))
    print('  currency       : {}'.format(currency))
    print('  csv outfile   : {}'.format(csv_out_file))
    print('  log outfile   : {}'.format(logfile))

    templates = load_yamlfile(template_file)
    buildings = load_yamlfile(building_file)
    efficiency = load_yamlfile(efficiency_file)
    workers = load_yamlfile(worker_file)
    market = Market(load_yamlfile(exchange_file), currency)

    return {
        'config-date': config_date,
        'templates': templates,
        'buildings': buildings,
        'efficiency': efficiency,
        'workers': workers,
        'market': market,
        'csv-out': csvout,
        'log': logout
    }

""" Creates a map of supply costs for each supply material 
"""
def create_supply_map(config):
    workers = config['workers']
    market = config['market']
    supply_map = {}
    for site_name in workers.keys():
        site = workers[site_name]
        for worker_type in site:
            worker = site[worker_type]
            if 'needs' in worker:
                for need in worker['needs']:
                    ticker = need['id']
                    price = market.price(ticker)
                    if ticker not in supply_map:
                        supply_map[ticker] = price.avg
    return supply_map

""" Creates a map of sourcing options (MKT and template-based) for each material
"""
def create_source_map(config):
    templates = config['templates']
    source_map = {}
    for key in templates.keys():
        template = templates[key]
        for input in template['inputs']:
            ticker = input['id']
            if ticker not in source_map: 
                source_map[ticker] = [ticker + ".MKT"]
        for output in template['outputs']:
            ticker = output['id']
            if ticker in source_map: 
                source_map[ticker].append(key)
            else:
                source_map[ticker] = [ticker + ".MKT", key]
    return source_map

""" Builds all input combinations for templates 
    Takes multiple sources into account for each input
    Options are input as Lists of Source Option Lists 
    
    Example:
    Template that takes two inputs with 3 and 2 sourcing options respectively:
       options = [[A, B, C], [M, N]]
    Results in 6 input combinations returned: 
       result = [ [A,M], [A,N], [B,M], [B,N], [C,M], [C, N] ] 
"""
def combine_options(options):
    combos = []
    if len(options) == 0:
        return []
    options = copy.copy(options)
    head = options.pop(0)
    if len(options) > 0:
        subcombos = combine_options(options)
        for option in head:
            for subcombo in subcombos: 
                combo = [option]
                combo.extend(subcombo)
                combos.append(combo)
    else:
        for option in head:
            combo = [option]
            combos.append(combo)
    return combos

TREE_CACHE = {}

""" Builds production trees for the provided key (aka template id)
    Returns all variants of possible production treess for a given template
"""
def build_prod_tree(config, key):
    if '.MKT' in key:
        return [ GraphNode(config, key, 0, []) ]
    if key in TREE_CACHE:
        return TREE_CACHE[key]

    trees = []
    sources = config['sources']
    template = config['templates'][key]

    if len(template['inputs']) == 0:
        trees.append(GraphNode(config, key, 0, []))
    else:
        # identify all input combinations and production trees
        input_options = []
        for input in template['inputs']:
            input_trees = []
            for source in sources[input['id']]:
                source_chain = build_prod_tree(config, source)
                input_trees.extend(source_chain)
            input_options.append(input_trees)
        input_combos = combine_options(input_options) 

        # create a production tree root for each variation
        variant = 0
        for combo in input_combos:
            combo_node = GraphNode(config, key, variant, combo)
            trees.append(combo_node)
            variant = variant + 1

    TREE_CACHE[key] = trees
    return trees

""" creates a new instance of supply based on calculated values from nodes
"""
def update_supply(config, nodes):
    orig_supply = config['supply']
    new_supply = copy.copy(orig_supply)
    # iterate through each production tree, finding the minimum value of each produced material 
    for template in nodes:
        primary_output = template.split(".")[0]
        if primary_output in orig_supply: 
            for variant in nodes[template]:
                if variant["total_cost_per_unit"] < new_supply[primary_output]:
                    new_supply[primary_output] = variant["total_cost_per_unit"]
    return new_supply

""" write the production trees out as a cvs file
"""
def write_csv(config, nodes):
    csvout = config['csv-out']
    header_written = False
    for template in nodes.keys():
        node_set = nodes[template]
        for node in node_set:
            if not header_written:
                print(node.to_csv_header(), file=csvout)
                header_written = True
            print(node.to_csv_record(), file=csvout)

""" runtime entrypoint 
"""
def main(argv):
    try:
        # initialize the app
        args = extract_args(argv)
        timestamp = datetime.now()
        config = load_config(args, timestamp)
        config['supply'] = create_supply_map(config)
        config['sources'] = create_source_map(config)
    
        sources_out = json.dumps(config['sources'], indent=2)
        print('sources:\n{}'.format(sources_out), file=config['log'])
        print("", file=config['log'])
        supply_out = json.dumps(config['supply'], indent=2)
        print('starting supply:\n{}'.format(supply_out), file=config['log'])

        # process input files to produce the graph
        # make multiple passes until supply costs stabilize
        processing = True
        templates = config['templates']
        start = datetime.utcnow().timestamp()
        print('start processing: {}'.format(start))
        nodes = {}
        cnt = 0
        while (processing):
            cnt = cnt + 1
            # supply_out = json.dumps(config['supply'])
            # print('pass {} supply:\n{}'.format(cnt, supply_out), file=config['log'])
            for key in templates.keys():
                nodes[key] = build_prod_tree(config, key)
            new_supply = update_supply(config, nodes)
            config['supply'] = new_supply
            if cnt >= 5:
                processing = False
            
        supply_out = json.dumps(config['supply'], indent=2)
        print('ending supply:\n{}'.format(supply_out), file=config['log'])

        end = datetime.utcnow().timestamp()
        delta = end - start
        print('end processing: {} \u0394 {:8.6f}'.format(end, delta))

        write_csv(config, nodes)

        done = datetime.utcnow().timestamp()
        delta = done - end
        print('outputs done: {} \u0394 {:8.6f}'.format(done, delta))

        tree_count = sum(map(lambda x: len(nodes[x]), nodes.keys()))
        print('{} production trees identified'.format(tree_count))

        print("done")

    except Exception:
        traceback.print_exc()
        return 100

if __name__ == '__main__':
    sys.exit(main(sys.argv))