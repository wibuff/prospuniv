#!/usr/bin/python3
""" query a YAML file using YAQL query syntax
"""
import sys
import traceback
from datetime import datetime
import yaql
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
from environment import DATA_DIR

def extract_args(argv):
    if len(argv) < 3:
        print('usage: {} <yaml-file> <query> [<output-type>]'.format(argv[0]))
        raise Exception("missing parms")
    return argv[1:]
    
def load_yaml(filename):
    with open(filename, 'r') as infile:
        return yaml.load(infile, Loader=Loader)    

def main(argv):
    """ runtime entrypoint """
    try:
        args = extract_args(argv)
        timestamp = datetime.now()
        source = load_yaml(args[0])
        query = args[1]
        output_type = 'DEFAULT'
        if len(args) > 2:
            output_type = args[2]

        engine = yaql.factory.YaqlFactory().create()

        expression = engine(query)
        results = expression.evaluate(data=source)

        if output_type == 'DEFAULT':
            print(results)
        elif output_type == 'YAML':
            output = yaml.dump(results, Dumper=Dumper, explicit_start=True)
            print(output)
        else:
            raise Exception('unknown output type {}'.format(output_type))
        return 0

    except Exception as err:
        traceback.print_exc()
        return 100

if __name__ == '__main__':
    sys.exit(main(sys.argv))