#!/usr/bin/python3
""" run all extracts from a game extract file
"""
import os
import sys

def extract_args(argv):
    if len(argv) < 2:
        print('usage: {} <YYYY-MM-DD>'.format(argv[0]))
        raise Exception("missing parms")
    return argv[1:]

def main(argv):
    """ runtime entrypoint """
    try:
        args = extract_args(argv)
        dt_tag = args[0]
        source = 'data/extract-{}.json'.format(dt_tag)
        exchange = 'data/exchange-{}.yaml'.format(dt_tag)
        inventory = 'data/inventory-{}.yaml'.format(dt_tag)
        sites = 'data/sites-{}.yaml'.format(dt_tag)
        templates = 'data/templates-{}.yaml'.format(dt_tag)
        orders = 'data/orders-{}.yaml'.format(dt_tag)
        orders_report = 'reports/orders-{}.yaml'.format(dt_tag)

        print('extracting all data for {}'.format(dt_tag))
        print('source file is {}'.format(source))
        if not os.path.isfile(source):
            raise Exception('ERROR {} not found'.format(source))

        status = os.system('src/extract-broker-data.py {} > {}'.format(source, exchange))
        print('extract exchange data, exit code={}'.format(status))

        status = os.system('src/extract-inventory-data.py {} > {}'.format(source, inventory))
        print('extract inventory data, exit code={}'.format(status))

        status = os.system('src/extract-site-data.py {} > {}'.format(source, sites))
        print('extract site data, exit code={}'.format(status))

        status = os.system('src/extract-template-data.py {} > {}'.format(source, templates))
        print('extract template data, exit code={}'.format(status))

        status = os.system('src/extract-order-data.py {} > {}'.format(source, orders))
        print('extract order data, exit code={}'.format(status))

        status = os.system('src/gen-order-report.py {} YAML > {}'.format(orders, orders_report))
        print('generate order report, exit code={}'.format(status))

        return 0

    except Exception as err:
        print(err)
        return 100

if __name__ == '__main__':
    sys.exit(main(sys.argv))
