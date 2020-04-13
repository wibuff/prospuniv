""" prospuniv configuration
"""
import sys
import json
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
from environment import DATA_DIR

def load_datafile(path):
    with open(path, 'r') as infile:
        return json.load(infile)    

def load_yamlfile(path):
    with open(path, 'r') as infile:
        return yaml.load(infile, Loader=Loader)    

Buildings = load_yamlfile(DATA_DIR + '/buildings.yaml')
ProductionLines = load_yamlfile(DATA_DIR + '/prodlines.yaml')
Recipes = load_yamlfile(DATA_DIR + '/recipes.yaml')
Workers = load_yamlfile(DATA_DIR + '/workers.yaml')
