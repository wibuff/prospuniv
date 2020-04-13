""" class for representing the market """

import sys
import json

class Price(object):
    """ Price Class
    """
    HEADER_FMT = '{:>12s} {:>12s} {:>12s} {:>12s}'.format('Last', 'Avg', 'Ask', 'Bid')


    def __init__(self, pricedata=None):
        self.last = 0
        self.avg = 0
        self.ask = 0
        self.bid = 0
        self.supply = 0
        self.demand = 0
        if pricedata:
            self.last = pricedata['last']
            self.avg = pricedata['avg']
            self.ask = pricedata['ask']
            self.bid = pricedata['bid']
            self.supply = pricedata['supply']
            self.demand = pricedata['demand']

    def _format_value(self, value):
        if value:
            return '{:>12.2f}'.format(value)
        return '{:>12s}'.format("---")

    def __str__(self):
        last = self._format_value(self.last)
        avg = self._format_value(self.avg)
        ask = self._format_value(self.ask)
        bid = self._format_value(self.bid)
        return '{} {} {} {}'.format(last, avg, ask, bid)

    def __repr__(self):
        return json.dumps({
            'last': self.last,
            'avg': self.avg,
            'ask': self.ask,
            'bid': self.bid,
            'supply': self.supply,
            'demand': self.demand
        })

    def _handle_none(self, val):
        if (val): 
            return val
        return 0.0

    def multiply(self, factor):
        newprice = {
            'last': self._handle_none(self.last) * factor,
            'avg': self._handle_none(self.avg) * factor,
            'ask': self._handle_none(self.ask) * factor,
            'bid': self._handle_none(self.bid) * factor,
            'supply': self.supply,
            'demand': self.demand
        }
        return Price(newprice)

    def add(self, price):
        newprice = {
            'last': self._handle_none(self.last) + self._handle_none(price.last),
            'avg': self._handle_none(self.avg) + self._handle_none(price.avg),
            'ask': self._handle_none(self.ask) + self._handle_none(price.ask),
            'bid': self._handle_none(self.bid) + self._handle_none(price.bid),
            'supply': self.supply,
            'demand': self.demand
        }
        return Price(newprice)

class Market(object):
    """ Market Class 
    """
    def __init__(self, marketdata, exchange):
        self.prices = {}
        for product in marketdata[exchange]['prices'].keys():
            pricedata = marketdata[exchange]['prices'][product]    
            self.prices[product] = Price(pricedata)

    def __str__(self):
        return json.dumps(self.prices)

    def price(self, product): 
        if product in self.prices: 
            return self.prices[product]
        raise Exception('price for {} not found in market'.format(product))



            
        