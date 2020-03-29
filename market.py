""" class for representing the market """

import sys
import json

class Price(object):
    """ Price Class
    """
    def __init__(self, pricedata):
        self.last = pricedata[0]
        self.ask = pricedata[1]
        self.bid = pricedata[2]
        self.avg = pricedata[3]

    def __str__(self):
        return json.dumps({
            'last': self.last,
            'ask': self.ask,
            'bid': self.bid,
            'avg': self.avg
        })

    def multiply(self, factor):
        newprice = [self.last, self.ask, self.bid, self.avg]
        multprice = list(map(lambda x: x*factor, newprice))
        return Price(multprice)

    def add(self, price):
        origprice = [self.last, self.ask, self.bid, self.avg]
        addprice = [price.last, price.ask, price.bid, price.avg]
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



            
        