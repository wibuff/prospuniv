""" prospuniv configuration
"""
import json
import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
from environment import DATA_DIR

def load_datafile(path):
    """ load a JSON file """
    with open(path, 'r') as infile:
        return json.load(infile)

def load_yamlfile(path):
    """ load a YAML file - also supports JSON files """
    with open(path, 'r') as infile:
        return yaml.load(infile, Loader=Loader)

Buildings = load_yamlfile(DATA_DIR + '/buildings.yaml')
Recipes = load_yamlfile(DATA_DIR + '/recipes.yaml')
Workers = load_yamlfile(DATA_DIR + '/workers.yaml')
