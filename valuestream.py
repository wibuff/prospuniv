""" Value Stream Class
"""

import sys
import json
from clock import IncrClock, Duration
from configuration import Buildings, ProductionLines, Workers, Recipes
from productionline import ProductionLine

class ValueStream(object):
    """ ValueStream class
    """

    def __init__(self, streamconfig, inventory, market, duration):
        self.inventory = inventory
        self.market = market
        self.duration = duration
        self.clock = IncrClock(duration)
        self.streamconfig = streamconfig
        self.lines = self._init_lines(self.streamconfig)
        
    def _init_lines(self, streamconfig):
        lines = []
        for line in streamconfig['productionLines']:
            pline = ProductionLine(line['lineId'], line['queue'], self.inventory)
            lines.append(pline)
        return lines
        
    def calc_output(self, starting, ending):
        net = {}
        for key in ending.keys(): 
            start_val = 0
            if key in starting:
                start_val = starting[key]
            net[key] = ending[key] - start_val
        return net

    def calc_mkt_value(self, net_prod):
        val = { 'last': 0.0, 'ask': 0.0, 'bid': 0.0, 'avg': 0.0 }
        for key in net_prod: 
            prod = net_prod[key]            
            if key in self.market['prices']: 
                prices = self.market['prices'][key]
                val['last'] = val['last'] + prod * prices[0]
                val['ask'] = val['ask'] + prod * prices[1]
                val['bid'] = val['bid'] + prod * prices[2]
                val['avg'] = val['avg'] + prod * prices[3]
            else: 
                raise Exception('missing market value for {}'.format(key))
        return val       

    def run(self):
        start_inv = json.loads(str(self.inventory))
        print('{}: running value stream "{}"'.format(self.clock, self.streamconfig['description']))
        print('{}: starting inventory {}'.format(self.clock, self.inventory))

        while self.clock.step():
            for line in self.lines:
                line.step(self.clock)
        for line in self.lines:
            line.step(self.clock)

        print('{}: ending inventory {}'.format(self.clock, self.inventory))
        
        end_inv = json.loads(str(self.inventory))
        output = self.calc_output(start_inv, end_inv)
        print('{}: total output {}'.format(self.clock, json.dumps(output)))

        mkt_value = self.calc_mkt_value(output)
        print('{}: market value {}'.format(self.clock, json.dumps(mkt_value)))
        

    