""" Value Stream Class
"""

import sys
import json
from datetime import datetime
from clock import IncrClock, Duration
from configuration import Buildings, ProductionLines, Workers, Recipes
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
        for line in streamconfig['productionLines']:
            print('{} configuring production line {}'.format(self.clock, line['lineId']))
            pline = ProductionLine(self.stream_id, line['lineId'], line['queue'], self.inventory, self.market, self.clock)
            lines.append(pline)
        return lines

    def run(self):
        start_inv = json.loads(str(self.inventory))
        lines = self._init_lines(self.streamconfig)

        print("")
        print('value stream {} started'.format(self.stream_id))
        print('{} running value stream "{}"'.format(self.clock, self.streamconfig['description']))
        print('{} starting inventory {}'.format(self.clock, start_inv))

        while self.clock.step():
            for line in lines:
                line.step(self.clock)
        for line in lines:
            line.step(self.clock)

        print('{} ending inventory {}'.format(self.clock, self.inventory))

        end_inv = json.loads(str(self.inventory))
        self.summarize_run(lines, start_inv, end_inv)
        
    def summarize_run(self, lines, start_inv, end_inv):
        print("")
        print("*** RUN SUMMARY {} ***".format(self.stream_id))
        print("")
        print("Inventories:")
        output = self.calc_output(start_inv, end_inv)
        print('starting inventory {}'.format(start_inv))
        print('ending inventory   {}'.format(end_inv))
        print('total output       {}'.format(json.dumps(output)))

        print("")
        print("Market Values:")
        mkt_values = self.calc_mkt_values(output)
        sfmt = '{label:<5s}\t{prices[last]:>10s}\t{prices[ask]:>10s}\t{prices[bid]:>10s}\t{prices[avg]:>10s}'
        fmt = '{label:>5s}\t{price.last:>10.2f}\t{price.ask:>10.2f}\t{price.bid:>10.2f}\t{price.avg:>10.2f}'
        print(sfmt.format(label='Item', prices={ 'last': 'Last', 'ask': 'Ask', 'bid': 'Bid', 'avg': 'Avg'}))
        print(fmt.format(label='Total', price=mkt_values['totals']))
        for key in mkt_values['subtotals']: 
            label = key
            if len(label) < 3: 
                label = label + " "
            print(fmt.format(label=label, price=mkt_values['subtotals'][key]))

        print("")
        print("Product Line Summaries:")
        stream_ledger = Ledger(self.stream_id, "RUN.TOTALS", self.market)
        for line in lines:
            stream_ledger.add_ledger(line.ledger)
            line.ledger.output_summary()
            print("")

        print("Value Stream Run Summary:")
        stream_ledger.output_summary(True)

    def calc_output(self, starting, ending):
        net = {}
        for key in ending.keys(): 
            start_val = 0
            if key in starting:
                start_val = starting[key]
            net[key] = ending[key] - start_val
        return net

    def calc_mkt_values(self, net_prod):
        total = Price([0.0,0.0,0.0,0.0])
        subtotals = {}
        for product in net_prod: 
            num_produced = net_prod[product]            
            if num_produced > 0:
                price = self.market.price(product)
                subtotal = price.multiply(num_produced)
                subtotals[product] = subtotal
                total = total.add(subtotal)
        return { "totals": total, "subtotals": subtotals }
   