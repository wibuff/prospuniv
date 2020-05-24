#!/usr/bin/python3
""" extract template (recipe) data from the prospu state object
"""
import sys
from datetime import datetime, date
from clock import Duration
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

def build_template(linetype, lineticker, recipe):
    template = {
        'name': recipe['name'],
        'line': lineticker,
        'line-name': linetype,
        'outputs': [],
        'inputs': []
    }
    for outfactor in recipe['outputFactors']:
        ticker = outfactor['material']['ticker']
        count = outfactor['factor']
        template['outputs'].append({ 'id': ticker, 'count': count })
        if outfactor['material']['name'] == recipe['name']:
            template['ticker'] = ticker
    for infactor in recipe['inputFactors']:
        ticker = infactor['material']['ticker']
        count = infactor['factor']
        template['inputs'].append({ 'id': ticker, 'count': count })

    efficiency = recipe['efficiency']

    seconds = int(recipe['duration']['millis']/1000 * efficiency)
    template['time'] = str(Duration(str(seconds)))

    return template

def lookup_ticker(site, name):
    for platform in site['platforms']:
        if platform['module']['reactorName'] == name:
            return platform['module']['reactorTicker']
    return None

def main(argv):
    """ runtime entrypoint """
    try:
        args = extract_args(argv)
        state_file = load_yaml(args[0])
        lines = state_file['production']['lines']['data']
        sites = state_file['sites']['sites']['index']['data']

        collection = {}

        for line_id in lines: 
            line = lines[line_id]
            siteId = line['siteId']
            site = sites[siteId]

            linetype = line['type']
            lineTicker = lookup_ticker(site, linetype)
            recipes = line['productionTemplates']
            for recipe in recipes:
                template = build_template(linetype, lineTicker, recipe)
                if template['ticker'] in collection:
                    collection[template['ticker']].append(template)
                else:
                    collection[template['ticker']] = [template]

        templates = {}
        for key in collection.keys(): 
            i = 1
            for template in collection[key]:
                templates[key + "." + str(i)] = template
                i = i + 1

        output = yaml.dump(templates, Dumper=Dumper, explicit_start=True)
        print(output)
        return 0

    except Exception as err:
        print(err)
        return 100

if __name__ == '__main__':
    sys.exit(main(sys.argv))