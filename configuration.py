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

def load_datafile(filename):
    path = DATA_DIR + "/" + filename
    with open(path, 'r') as infile:
        return json.load(infile)    

def load_yamlfile(filename):
    path = DATA_DIR + "/" + filename
    with open(path, 'r') as infile:
        return yaml.load(infile, Loader=Loader)    

Buildings = load_yamlfile('buildings.yaml')
ProductionLines = load_yamlfile('prodlines.yaml')
Recipes = load_yamlfile('recipes.yaml')
Workers = load_yamlfile('workers.yaml')
