""" class for representing the market """

import sys
import json

class Price(object):
    """ Price Class
    """
    HEADER_FMT = '{:>12s} {:>12s} {:>12s} {:>12s}'.format('Last', 'Avg', 'Ask', 'Bid')


    def __init__(self, pricedata):
        self.last = pricedata[0]
        self.avg = pricedata[1]
        self.ask = pricedata[2]
        self.bid = pricedata[3]

    def __str__(self):
        return '{0.last:12.2f} {0.avg:12.2f} {0.ask:12.2f} {0.bid:12.2f}'.format(self)

    def __repr__(self):
        return json.dumps({
            'last': self.last,
            'avg': self.avg,
            'ask': self.ask,
            'bid': self.bid
        })
    def multiply(self, factor):
        newprice = [self.last, self.avg, self.ask, self.bid]
        multprice = list(map(lambda x: x*factor, newprice))
        return Price(multprice)

    def add(self, price):
        origprice = [self.last, self.avg, self.ask, self.bid]
        addprice = [price.last, price.avg, price.ask, price.bid]
        newprice = list(map(sum, zip(origprice, addprice)))
        return Price(newprice)

class Market(object):
    """ Market Class 
    """
    def __init__(self, marketdata):
        self.prices = {}
        for product in marketdata['prices'].keys():
            pricedata = marketdata['prices'][product]    
            self.prices[product] = Price(pricedata)

    def __str__(self):
        return json.dumps(self.prices)

    def price(self, product): 
        if product in self.prices: 
            return self.prices[product]
        raise Exception('price for {} not found in market'.format(product))



            
        