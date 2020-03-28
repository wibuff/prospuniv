""" prospuniv configuration
"""
import sys
import json
from environment import DATA_DIR

def load_datafile(filename):
    path = DATA_DIR + "/" + filename
    with open(path, 'r') as infile:
        return json.load(infile)    

Buildings = load_datafile('buildings.json')
ProductionLines = load_datafile('prodlines.json')
Recipes = load_datafile('recipes.json')
Workers = load_datafile('workers.json')
