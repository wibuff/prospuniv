""" Value Stream Class
"""

import sys
import json
from datetime import datetime
from clock import IncrClock, Duration
from configuration import Buildings, ProductionLines, Workers, Recipes
from inventory import Inventory
from productionline import ProductionLine
from market import Price
from ledger import Ledger

class ValueStream(object):
    """ ValueStream class
    """
    def __init__(self, streamconfig, inventory, market, duration):
        self.stream_id = '{:%Y%m%d.%H%M%S.%f}'.format(datetime.now())
        print("")
        print('value stream {} initializing'.format(self.stream_id))
        self.inventory = inventory
        self.market = market
        self.duration = duration
        self.clock = IncrClock(duration)
        self.streamconfig = streamconfig
        
    def _init_lines(self, streamconfig):
        lines = []
        for line_spec in streamconfig['productionLines']:
            pline = ProductionLine(self.stream_id, line_spec, self.inventory, self.market, self.clock)
            lines.append(pline)
        return lines

    def run(self):
        start_inv = Inventory(json.loads(str(self.inventory)))
        lines = self._init_lines(self.streamconfig)

        print("")
        print('{} value stream {} run started'.format(self.clock, self.stream_id))
        print('{} description "{}"'.format(self.clock, self.streamconfig['description']))

        while self.clock.step():
            for line in lines:
                line.step(self.clock)
        for line in lines:
            line.step(self.clock)

        print('{} value stream {} run complete'.format(self.clock, self.stream_id))
        end_inv = Inventory(json.loads(str(self.inventory)))
        self.summarize_run(lines, start_inv, end_inv)
        
    def summarize_run(self, lines, start_inv, end_inv):
        print('')
        print('*** RUN SUMMARY {} ***'.format(self.stream_id))
        print('')

        print('Value Stream Summary:')
        stream_ledger = Ledger(self.stream_id, 'RUN.TOTALS', self.market)
        for line in lines:
            stream_ledger.add_ledger(line.ledger)
        stream_ledger.output_summary()

        print('')
        print('Production Line Summaries:')
        for line in lines:
            line.ledger.output_summary()
            print("")

        print('Inventory Summaries:')
        start_inv.output_summary('Starting Assets', self.market)
        end_inv.output_summary('Ending Assets', self.market)
        net_inv = end_inv.diff(start_inv)
        net_inv.output_summary('Asset Changes', self.market)
        
    def calc_output(self, starting, ending):
        net = {}
        for key in ending.keys(): 
            start_val = 0
            if key in starting:
                start_val = starting[key]
            net[key] = ending[key] - start_val
        return net

    def calc_mkt_values(self, net_prod):
        total = Price()
        subtotals = {}
        for product in net_prod: 
            num_produced = net_prod[product]            
            if num_produced > 0:
                price = self.market.price(product)
                subtotal = price.multiply(num_produced)
                subtotals[product] = subtotal
                total = total.add(subtotal)
        return { "totals": total, "subtotals": subtotals }
   