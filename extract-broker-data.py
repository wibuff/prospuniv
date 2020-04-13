#!/usr/bin/python3
""" extract broker data from the prospu state object
"""
import sys
from datetime import datetime
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
from environment import DATA_DIR

def extract_args(argv):
    if len(argv) < 2:
        print('usage: {} <state-file>',format(argv[0]))
        raise Exception("missing parms")
    return argv[1:]
    
def load_yaml(filename):
    with open(filename, 'r') as infile:
        return yaml.load(infile, Loader=Loader)    

def load_categories(state):
    categories = {}
    for category in state['materials']['categories']:
        categories[category['id']] = category['name']
    return categories

def load_exchanges(state):
    exchanges = {}
    exchange_data = state['comex']['exchange']['exchanges']['data']
    for exchange in exchange_data:
        exchanges[exchange_data[exchange]['code']] = {
            'code': exchange_data[exchange]['code'],
            'name': exchange_data[exchange]['name'],
            'currency': exchange_data[exchange]['currency']['code'],
            'timestamp': '{}'.format(datetime.now()),
            'prices': {}
        }
    return exchanges

def build_price(broker_data):
    price = {
        "last": None,
        "ask": None,
        "bid": None,
        "avg": None,
        "supply": None,
        "demand": None,
    }
    if broker_data['price']:
        price['last'] = float(broker_data['price']['amount'])
    if broker_data['ask']:
        price['ask'] = float(broker_data['ask']['price']['amount'])
    if broker_data['bid']:
        price['bid'] = float(broker_data['bid']['price']['amount'])
    if broker_data['priceAverage']:
        price['avg'] = float(broker_data['priceAverage']['amount'])
    if broker_data['supply']:
        price['supply'] = broker_data['supply']
    if broker_data['demand']:
        price['demand'] = broker_data['demand']
    return price
    
def load_prices(brokers): 
    exchange_prices = {}
    for broker in brokers.keys():
        data = brokers[broker]['data']
        ticker = data['material']['ticker']
        price = build_price(data)

        exchange = data['exchange']['code']
        if exchange not in exchange_prices:
            exchange_prices[exchange] = {}
        exchange_prices[exchange][ticker] = price
    return exchange_prices

def main(argv):
    """ runtime entrypoint """
    try:
        args = extract_args(argv)
        timestamp = datetime.now()
        state_file = load_yaml(args[0])
        exchanges = load_exchanges(state_file)

        prices = load_prices(state_file['comex']['broker']['brokers'])
        for exchange_code in exchanges.keys():
            exchange = exchanges[exchange_code]
            if exchange_code in prices:
                exchange['prices'] = prices[exchange_code]

        output = yaml.dump(exchanges, Dumper=Dumper, explicit_start=True)
        print(output)

    except Exception as err:
        print(err)
        return 100

if __name__ == '__main__':
    sys.exit(main(sys.argv))