#!/usr/bin/python3
""" generate a report of all orders 
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
    if len(argv) < 2:
        print('usage: {} <order-file> [<output-type>]'.format(argv[0]))
        raise Exception("missing parms")
    return argv[1:]
    
def load_yaml(filename):
    with open(filename, 'r') as infile:
        return yaml.load(infile, Loader=Loader)    

def summarize_order_type(engine, source, order_type):
    ticker = order_type[0]
    trx_type = order_type[1]

    order_query_str = '$.where($.ticker={}).where($.type={})'.format(ticker, trx_type)
    max_query_str = '$.where($.ticker={}).where($.type={}).select([$.amount]).selectMany($).max()'.format(ticker, trx_type)
    min_query_str = '$.where($.ticker={}).where($.type={}).select([$.amount]).selectMany($).min()'.format(ticker, trx_type)
    sum_query_str = '$.where($.ticker={}).where($.type={}).select([$.amount]).selectMany($).sum()'.format(ticker, trx_type)
    count_query_str = '$.where($.ticker={}).where($.type={}).select([$.amount]).selectMany($).count()'.format(ticker, trx_type)

    order_query = engine(order_query_str)
    max_query = engine(max_query_str)
    min_query = engine(min_query_str)
    sum_query = engine(sum_query_str)
    count_query = engine(count_query_str)

    order_type_records = order_query.evaluate(data=source)
    max_val = max_query.evaluate(data=order_type_records)
    min_val = min_query.evaluate(data=order_type_records)
    sum_val = sum_query.evaluate(data=order_type_records)
    count = count_query.evaluate(data=order_type_records)
    avg = float(sum_val) / float(count)

    return {
        'ticker': ticker,
        'type': trx_type,
        'count': count,
        'avg': avg,
        'min': min_val,
        'max': max_val
    }

def main(argv):
    """ runtime entrypoint """
    try:
        args = extract_args(argv)
        timestamp = datetime.now()
        source = load_yaml(args[0])
        output_type = 'DEFAULT'
        if len(args) > 1:
            output_type = args[1]

        results = []
        engine = yaql.factory.YaqlFactory().create()
        order_type_query = engine('$.select([$.ticker,$.type]).distinct().orderBy($[0])')
        order_types = order_type_query.evaluate(data=source)

        for order_type in order_types: 
            results.append(summarize_order_type(engine, source, order_type))

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